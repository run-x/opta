resource "null_resource" "local-base" {

  provisioner "local-exec" {
    command = "/bin/bash 'install_software.sh'"
  }
  provisioner "local-exec" {
    when    = destroy
    command = <<EOT
        echo "Uninstalling kind"
        rm -rf ~/.opta/kind
        echo "Stopping and removing local docker registry"
        docker stop opta-local-registry
        docker rm opta-local-registry
    EOT

    working_dir = path.module
  }
}
