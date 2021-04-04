set -euo

# Filename of the triggered workflow.
workflow="$1"

get_latest_build_data() {
  latest_build=$(curl -X GET "https://api.github.com/repos/run-x/runxc/actions/workflows/${workflow}/runs" \
  -H 'Accept: application/vnd.github.antiope-preview+json' \
  -H "Authorization: Bearer ${github_token}" | jq '[.workflow_runs[]] | first')
  echo "$latest_build"
}

previous_build=$(get_latest_build_data)
previous_build_id=$(echo $previous_build | jq '.id')

# Trigger new workflow build
curl -X POST "https://api.github.com/repos/run-x/runxc/actions/workflows/${workflow}/dispatches" \
-H "Accept: application/vnd.github.v3+json" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${github_token}" \
--data '{"ref":"main"}'

# Wait for the build to start.
latest_build_id=""
while [[ -z "$latest_build_id" || "$latest_build_id" == "$previous_build_id" ]]; do
  echo "Waiting for build to start..."
  sleep 5
  latest_build=$(get_latest_build_data)
  latest_build_id=$(echo $latest_build | jq '.id')
done

echo "The ID of the newly created build is [$latest_build_id]"

# Wait for the build to finish.
conclusion="null"
status="n/a"
while [[ $conclusion == "null" && $status != "\"completed\"" ]]; do
  echo "Waiting for build to finish..."
  sleep 120
  current_build=$(get_latest_build_data)
  conclusion=$(echo $current_build | jq '.conclusion')
  status=$(echo $current_build | jq '.status')
  echo "Checking conclusion [$conclusion]"
  echo "Checking status [$status]"
done

# Exit with error code if the triggerd build failed.
if [[ $conclusion == "\"success\"" && $status == "\"completed\"" ]]
then
  echo "The triggered build completed successfully."
else
  echo "The triggered build failed."
  exit 1
fi
