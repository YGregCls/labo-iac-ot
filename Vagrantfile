Vagrant.configure("2") do |config|

  # Image Linux de base
  config.vm.box = "bento/ubuntu-24.04"

  # Nom de la machine
  config.vm.hostname = "ctrl"

  # Configuration VMware
  config.vm.provider "vmware_desktop" do |vmware|
    vmware.vmx["memsize"] = "2048"
    vmware.vmx["numvcpus"] = "2"

    # Emplacement des machines virtuelles
    vmware.clone_directory = "D:/Labo-IaC-OT/vms"
  end

end