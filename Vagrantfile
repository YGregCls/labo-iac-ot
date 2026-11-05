
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

  # Cette machine accueille :
  #
  # - OpenPLC Runtime v4
  # - Le programme industriel Ladder
  # - Le serveur Modbus TCP (port 5020)
  # - Les variables industrielles simulees
  #
  # Elle appartient a la zone OT / PROCESS.
  #
  # Reseau industriel :
  # 192.168.100.0/24
  #
  # IMPORTANT :
  # Cette VM est deja fonctionnelle.
  # Sa configuration existante doit etre preservee.
  #
  # autostart: false permet de ne pas demarrer
  # automatiquement cette VM avec "vagrant up".

  config.vm.define "ot-process", autostart: false do |process|

    # Nom de la machine dans Ubuntu
    process.vm.hostname = "ot-process"

    # Interface du reseau industriel PROCESS
    # Reseau VMware VMnet3 : 192.168.100.0/24
    # Adresse statique de la machine OT-PROCESS

    process.vm.network "private_network",
      ip: "192.168.100.10",
      netmask: "255.255.255.0"

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

  # ==================================================
  # VM 3 : OT-ADMIN - POSTE D'ADMINISTRATION OT
  # ==================================================

  # Cette machine accueillera :
  #
  # - Un environnement graphique XFCE
  # - Un navigateur pour administrer pfSense
  # - Des clients SSH
  # - Des outils de diagnostic reseau
  # - Des outils d'administration industrielle
  #
  # Elle appartient a la zone ADMIN.
  #
  # Reseau administratif :
  # VMware VMnet2 : 192.168.56.0/24
  #
  # Adresse IP statique :
  # 192.168.56.20
  #
  # L'environnement graphique sera installe
  # automatiquement avec Ansible.
  #
  # IMPORTANT :
  # La configuration du pare-feu pfSense sera
  # realisee progressivement.
  #
  # Aucune passerelle statique vers pfSense
  # n'est imposee lors de la creation de la VM.
  #
  # autostart: false permet de demarrer cette VM
  # uniquement lorsque cela est necessaire.

  config.vm.define "ot-admin", autostart: false do |admin|

    # Nom de la machine dans Ubuntu
    admin.vm.hostname = "ot-admin"

    # Interface du reseau d'administration OT
    # Reseau VMware VMnet2 : 192.168.56.0/24
    # Adresse statique du poste d'administration

    admin.vm.network "private_network",
      ip: "192.168.56.20",
      netmask: "255.255.255.0"

    # Configuration VMware
    admin.vm.provider "vmware_desktop" do |vmware|

      # Memoire RAM : 4 Go
      vmware.vmx["memsize"] = "4096"

      # Processeurs virtuels : 2
      vmware.vmx["numvcpus"] = "2"

      # Emplacement des machines virtuelles
      vmware.clone_directory = "D:/Labo-IaC-OT/vms"

    end

  end

  # ==================================================
  # PARE-FEU : FW-OT-01
  # ==================================================

  # Pare-feu virtuel :
  # pfSense Community Edition 2.7.2
  #
  # Deploiement actuel :
  # Creation manuelle dans VMware Workstation.
  #
  # Interfaces :
  #
  # WAN     : VMnet8 - 192.168.75.0/24
  # ITIaC   : VMnet1 - 192.168.154.254/24
  # ADMINIaC: VMnet2 - 192.168.56.254/24
  # OTIaC   : VMnet3 - 192.168.100.254/24
  # DMZIaC  : VMnet4 - 192.168.110.254/24
  #
  

end
