Packaging
=========
- Create a new release with a new tag (0.<x>.<y>)
- This will trigger the `package` github action, which creates the binary and upload it to S3
- Update the `latest` file to point to the new release in the S3 bucket
- In the release, provide the s3 urls and also write a changelog based on the commits since the last release
- Update the docs website to point to this latest release
