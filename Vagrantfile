
Vagrant.configure("2") do |config|

  # ==================================================
  # PROJET : LABO IaC OT
  # Infrastructure industrielle automatisee
  # Hyperviseur : VMware Workstation
  # Systeme : Ubuntu 24.04
  # ==================================================

  # Image Linux commune aux machines virtuelles
  config.vm.box = "bento/ubuntu-24.04"

  # ==================================================
  # VM 1 : CTRL - NOEUD DE CONTROLE ANSIBLE
  # ==================================================

  # IMPORTANT :
  # On conserve le nom Vagrant "default" afin de
  # reutiliser notre machine virtuelle existante.
  #
  # Son hostname Linux reste "ctrl".
  # Elle contient deja notre installation Ansible,
  # nos inventaires et nos premiers playbooks.

  config.vm.define "default", primary: true do |ctrl|

    # Nom de la machine dans Ubuntu
    ctrl.vm.hostname = "ctrl"

    # Interface de gestion du laboratoire IaC OT
    # Reseau VMware VMnet2 : 192.168.56.0/24
    # Adresse statique pour l'administration Ansible

    ctrl.vm.network "private_network",
      ip: "192.168.56.10",
      netmask: "255.255.255.0"

    # Configuration VMware
    ctrl.vm.provider "vmware_desktop" do |vmware|

      # Memoire RAM : 2 Go
      vmware.vmx["memsize"] = "2048"

      # Processeurs virtuels : 2
      vmware.vmx["numvcpus"] = "2"

      # Emplacement des machines virtuelles
      vmware.clone_directory = "D:/Labo-IaC-OT/vms"

    end

  end

  # ==================================================
  # VM 2 : OT-PROCESS - SIMULATION INDUSTRIELLE
  # ==================================================

  # Cette machine accueillera progressivement :
  #
  # - OpenPLC
  # - Une simulation de processus industriel
  # - Un serveur Modbus TCP
  # - Des variables industrielles simulees
  #
  # Elle appartiendra a la zone PROCESS.
  #
  # Reseau cible :
  # 192.168.100.0/24
  #
  # IMPORTANT :
  # L'interface reseau industrielle sera configuree
  # apres validation de notre architecture VMware.

  # autostart: false permet de ne pas demarrer
  # automatiquement cette VM avec "vagrant up".

  config.vm.define "ot-process", autostart: false do |process|

    # Nom de la machine dans Ubuntu
    process.vm.hostname = "ot-process"

    # Configuration VMware
    process.vm.provider "vmware_desktop" do |vmware|

      # Memoire RAM : 2 Go
      vmware.vmx["memsize"] = "2048"

      # Processeurs virtuels : 2
      vmware.vmx["numvcpus"] = "2"

      # Emplacement des machines virtuelles
      vmware.clone_directory = "D:/Labo-IaC-OT/vms"

    end

  end

end
