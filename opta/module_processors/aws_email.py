from typing import TYPE_CHECKING, List, Optional

import boto3
from botocore.config import Config
from click import prompt
from colored import attr, fg
from email_validator import EmailNotValidError, validate_email
from mypy_boto3_sesv2.client import SESV2Client

from opta.exceptions import UserErrors
from opta.module_processors.base import ModuleProcessor
from opta.utils import logger

if TYPE_CHECKING:
    from opta.layer import Layer
    from opta.module import Module


class AwsEmailProcessor(ModuleProcessor):
    def __init__(self, module: "Module", layer: "Layer"):
        if (module.aliased_type or module.type) != "aws-email":
            raise Exception(
                f"The module {module.name} was expected to be of type aws email"
            )
        if layer.parent is not None:
            raise UserErrors(
                "Aws email must be set on a per environment level-- makes no sense to have it per service."
            )
        self.read_buckets: List[str] = []
        self.write_buckets: List[str] = []
        super(AwsEmailProcessor, self).__init__(module, layer)

    def process(self, module_idx: int) -> None:
        dns_modules = self.layer.get_module_by_type("aws-dns", module_idx)

        if len(dns_modules) == 0:
            raise UserErrors("AWS email needs the dns to be setup and delegated to work")
        dns_module = dns_modules[0]
        if not dns_module.data.get("delegated", False):
            raise UserErrors("AWS email needs the dns to be setup and delegated to work")
        self.module.data["domain"] = f"${{{{module.{dns_module.name}.domain}}}}"
        self.module.data["zone_id"] = f"${{{{module.{dns_module.name}.zone_id}}}}"
        super(AwsEmailProcessor, self).process(module_idx)

    def post_hook(self, module_idx: int, exception: Optional[Exception]) -> None:
        if exception is not None:
            return
        providers = self.layer.gen_providers(0)
        region = providers["provider"]["aws"]["region"]
        sesv2_client: SESV2Client = boto3.client(
            "sesv2", config=Config(region_name=region)
        )
        ses_account = sesv2_client.get_account()

        if ses_account["ProductionAccessEnabled"]:
            logger.info("Alrighty, looks like your account is out of SES sandbox")
            return
        elif "Details" in ses_account:
            if ses_account["Details"]["ReviewDetails"]["Status"] == "PENDING":
                logger.info(
                    f"{fg(5)}{attr(1)}Looks like review for taking you out of the SES sandbox is still pending. You can "
                    f"follow it in your AWS Support Cases (e.g. go to the AWS UI aka console and at the top search bar look "
                    f"for \"support\")-- your case id is {ses_account['Details']['ReviewDetails']['CaseId']}{attr(0)}"
                )
                return
            elif (
                ses_account["Details"]["ReviewDetails"]["Status"] == "FAILED"
                or ses_account["Details"]["ReviewDetails"]["Status"] == "DENIED"
            ):
                logger.warning(
                    f"{fg(5)}{attr(1)}Crap, not good, looks like your request to move out of the SES sandbox has been "
                    f"denied/failed-- you're gonna need to go resolve this manually in your support case. This is how "
                    f"you do it: go to our AWS Support Cases (e.g. go to the AWS UI aka console and at the top search "
                    f"bar look for \"support\")-- your case id is {ses_account['Details']['ReviewDetails']['CaseId']} "
                    f"odds are someone in AWS customer service responded to it. Just click on it, and nicely answer the "
                    f"human's questions/concerns to get your access approved.{attr(0)}"
                )
                return

        logger.info(
            f"{fg(5)}{attr(1)}Alright, if you're seeing this message in your terminal, there's a little bit more setup "
            f"which we're going to guide you through. So with its email service Amazon is a little bit freaked out that "
            f"folks would use it for spam and what not from bot-created accounts. To address this issue, all AWS accounts "
            f'start with "sandboxed" email service, meaning they can only send emails to verified accounts. A user would '
            f"then make a special request via the AWS console to get out of the sandbox mode. You can read "
            f"more about it here https://docs.aws.amazon.com/ses/latest/DeveloperGuide/request-production-access.html. "
            f"Of course, that is terrible user experience, so opta is here to help! We'll submit the form for you"
            f"but we need you to fill in a few things now.{attr(0)}"
        )
        website_url = ""
        while website_url == "":
            website_url = prompt(
                "Please enter your official website url-- the most official thing to show the AWS folks that this is for real.",
                type=str,
            ).strip()
        if not website_url.startswith("https://"):
            website_url = f"https://{website_url}"
        description = ""
        while description == "":
            description = prompt(
                "Please enter some brief description about why you want this email capability",
                type=str,
            ).strip()
        email_list: List[str] = []
        valid_emails = False
        while not valid_emails:
            email_list = []
            contact_emails: str = prompt(
                "Please enter a comma-delimited list of contact emails to keep in the loop about this request (need at least one).",
                type=str,
            )
            potential_emails = contact_emails.split(",")
            valid_emails = True
            for potential_email in potential_emails:
                try:
                    valid = validate_email(potential_email.strip())
                    email_list.append(valid.email)
                except EmailNotValidError as e:
                    logger.warning(str(e))
                    valid_emails = False

        sesv2_client.put_account_details(
            MailType="TRANSACTIONAL",
            WebsiteURL=website_url,
            ContactLanguage="EN",
            UseCaseDescription=description,
            AdditionalContactEmailAddresses=email_list,
            ProductionAccessEnabled=True,
        )
        logger.info(
            "Alright, SES accoount upgrade from sandbox request is sent. Give AWS ~24 hours to resolve this issue "
            "(the emails we asked you to include will be kept in the loop and should already have an email sent). "
            "You can keep using opta in the mean time and opta will print logs stating the status of your request so far"
        )
