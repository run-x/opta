import importlib
from typing import Dict

from modules.base import ModuleProcessor

PROCESSOR_DICT: Dict[str, str] = {
    "aws-k8s-service": "AwsK8sServiceProcessor",
    "aws-k8s-base": "AwsK8sBaseProcessor",
    "datadog": "DatadogProcessor",
    "gcp-k8s-base": "GcpK8sBaseProcessor",
    "gcp-k8s-service": "GcpK8sServiceProcessor",
    "gcp-gke": "GcpGkeProcessor",
    "aws-dns": "AwsDnsProcessor",
    "aws-documentdb": "AwsDocumentDbProcessor",
    "runx": "RunxProcessor",
    "helm-chart": "HelmChartProcessor",
    "aws-iam-role": "AwsIamRoleProcessor",
    "aws-iam-user": "AwsIamUserProcessor",
    "aws-eks": "AwsEksProcessor",
    "aws-ses": "AwsEmailProcessor",
    "aws-sqs": "AwsSqsProcessor",
    "aws-sns": "AwsSnsProcessor",
    "azure-base": "AzureBaseProcessor",
    "azure-k8s-base": "AzureK8sBaseProcessor",
    "azure-k8s-service": "AzureK8sServiceProcessor",
    "local-k8s-service": "LocalK8sServiceProcessor",
    "external-ssl-cert": "ExternalSSLCert",
    "aws-s3": "AwsS3Processor",
    "gcp-dns": "GCPDnsProcessor",
    "gcp-service-account": "GcpServiceAccountProcessor",
    "custom-terraform": "CustomTerraformProcessor",
    "aws-dynamodb": "AwsDynamodbProcessor",
    "mongodb-atlas": "MongodbAtlasProcessor",
    "cloudfront-distribution": "AwsCloudfrontDstributionProcessor",
    "lambda-function": "LambdaFunctionProcessor",
}

# Relies on the python file being module_some_name.py, and then 
# the opta module file being named module-some-name
def generate_pymodule_path(module_type: str) -> str:
    base_name = "_".join(module_type.split("-"))
    return ".".join(["modules", base_name, base_name])


def get_processor_class(module_type: str) -> ModuleProcessor:
    try:
        pymodule_path = generate_pymodule_path(module_type)
        pymodule = importlib.import_module(pymodule_path)
    except ModuleNotFoundError:
        return ModuleProcessor

    return pymodule.__dict__[PROCESSOR_DICT[module_type]]
