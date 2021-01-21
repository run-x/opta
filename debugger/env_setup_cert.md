Ah, a problem with certs!

So ACM is AWS' ssl certificate management system which works great with the AWS load balancers and such but
(rubs forehead and sighs) purposefully can't be exported to work with anything else. Luckily for us we just
use it with their load balancers. 

So, important point: in order for the ACM to be verified (and therefore actually work), AWS checks to see if you
are the owner of the domain (only the owner of the domain can get ssl for it-- that's part of its point).
One of ways it does this (the way we're using) is by asking the creator to create special dns records with random
prefixes and special values on whatever is responsible for the domain in question. The ssl provider (ACM) then 
periodically queries the web for the new dns records which would only appear if the owner of the domain actually
set it as instructed. This is called domain validated certificates.

Fortunately for you, dear customers, we automate this away as much as possible by using the domain you specified
to create a Route53 hosted zone and automatically creating the needed dns records there for the verification. 
99% of the time, the reason ACM is stalling with the certs is because this hosted zone is the official owner of its
domain yet. In order to do so, you will need to set dns delegation for your new domain
(e.g. https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/CreatingNewSubdomain.html -- this process is not AWS
specific, it should work just fine if the parent is at Google Domains, godaddy, etc...). You can verify that it works
by doing the command `dig YOUR_DOMAIN NS` and see if it matches the NS records in the route53 hosted zone we created 
for you.

You can read more about ACM certs at https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html