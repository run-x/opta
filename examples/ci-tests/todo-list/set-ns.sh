CONFIGURATION_FILE=$1
# Set the Default Zone
export AWS_DEFAULT_REGION="us-east-2"

echo "Hosted Zone Id for optaci.com: $HOSTED_ZONE_ID_OPTA_CI"

DIRTY_ZONE_ID="{$(./dist/opta/opta output -c "$CONFIGURATION_FILE" | grep "zone_id")}"
ZONE_ID=$(echo "$DIRTY_ZONE_ID" | jq -r ".zone_id")

RECORD_SETS=$(aws route53 list-resource-record-sets --hosted-zone "$ZONE_ID")
NS_RECORD=$(echo "$RECORD_SETS" | jq ".ResourceRecordSets" | jq -c '.[] | select(.Type == "NS")')

CHANGED_BATCH="{
    \"Comment\": \"Add Nameserver to master Hosted Zone\",
    \"Changes\": [
        {
            \"Action\": \"UPSERT\",
            \"ResourceRecordSet\": $NS_RECORD
        }
    ]
}"

aws route53 change-resource-record-sets --hosted-zone "$HOSTED_ZONE_ID_OPTA_CI" --change-batch "$CHANGED_BATCH"
sleep 300
