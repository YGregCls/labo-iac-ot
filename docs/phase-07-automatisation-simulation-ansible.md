
# Phase 07 — Automatisation de la simulation Python avec Ansible

## 1. Objectif

Cette phase a pour objectif d'automatiser la préparation de
l'environnement Python utilisé pour la simulation industrielle
du laboratoire IaC OT.

La phase 06 a permis de mettre en place une communication Modbus TCP
entre un simulateur Python et OpenPLC Runtime v4.

La phase 07 vise à rendre cette préparation reproductible et
maintenable grâce à Ansible.

Les objectifs sont :

- Automatiser l'installation des dépendances système.
- Automatiser la création de l'environnement virtuel Python.
- Installer les bibliothèques définies dans requirements.txt.
- Vérifier la présence des fichiers du simulateur.
- Contrôler le bon fonctionnement de PyModbus.
- Garantir l'idempotence du playbook.
- Préserver la simulation industrielle existante.

Le lancement du simulateur reste manuel à ce stade.

## 2. Architecture technique

### Machine de contrôle

Nom : ctrl

Système : Ubuntu 24.04

Rôle :
- Administration du laboratoire.
- Exécution d'Ansible.
- Hébergement du simulateur Python.
- Client Modbus TCP.

Adresses :
- NAT : 192.168.75.134
- Administration : 192.168.56.10

### Machine industrielle

Nom : ot-process

Système : Ubuntu 24.04

Rôle :
- Hébergement d'OpenPLC Runtime v4.
- Exécution du programme Ladder.
- Serveur Modbus TCP.

Adresses :
- NAT : 192.168.75.135
- Réseau industriel : 192.168.100.10

Services :
- OpenPLC Runtime : TCP 8443
- Modbus TCP : TCP 5020

### Communication industrielle

Le simulateur Python fonctionne actuellement sur ctrl.

Il communique avec OpenPLC par le réseau NAT.

Destination :

192.168.75.135:5020

Le déplacement du simulateur vers le réseau industriel
192.168.100.0/24 reste une évolution future.

## 3. Organisation des fichiers

Le projet utilise les fichiers suivants :

| Fichier | Fonction |
|---|---|
| ansible/inventory.ini | Inventaire Ansible |
| ansible/playbooks/07_preparation_simulation_python.yml | Préparation automatisée |
| simulation/requirements.txt | Dépendances Python |
| simulation/simulateur_cuve.py | Simulation industrielle |
| docs/phase-07-automatisation-simulation-ansible.md | Documentation de la phase |

L'environnement virtuel Python est situé sur ctrl :

/home/vagrant/venv-simulation-ot

Il n'est pas stocké dans le dépôt Git.

## 4. Configuration de l'inventaire Ansible

Le groupe controllers contient la machine ctrl.

Configuration :

```ini
[controllers]
ctrl ansible_connection=local ansible_python_interpreter=/usr/bin/python3.12
```

Ansible exécute les tâches directement sur ctrl.

La machine ot-process appartient au groupe process.

Elle n'est pas modifiée par le playbook de cette phase.

## 5. Préparation automatisée de Python

Playbook :

ansible/playbooks/07_preparation_simulation_python.yml

### Vérification des fichiers

Le module ansible.builtin.stat contrôle la présence de :

- simulation/simulateur_cuve.py
- simulation/requirements.txt

Le module ansible.builtin.assert valide ces prérequis.

Si un fichier obligatoire manque, le playbook échoue
avec un message explicite.

### Installation des dépendances système

Le module ansible.builtin.apt vérifie la présence de :

- python3
- python3-venv

Le paramètre state: present garantit que les paquets
sont installés sans réinstallation inutile.

Cette tâche utilise become: true pour obtenir les
privilèges administrateur.

### Création de l'environnement virtuel

L'environnement virtuel est créé dans :

/home/vagrant/venv-simulation-ot

Le module ansible.builtin.command exécute
python3 -m venv.

Le paramètre creates empêche la recréation de
l'environnement lorsque son exécutable Python existe déjà.

### Installation des bibliothèques

Le module ansible.builtin.pip utilise le fichier :

simulation/requirements.txt

Dépendance déclarée :

```text
pymodbus==3.16.1
```

L'installation est effectuée dans l'environnement virtuel.

### Vérification de PyModbus

Une commande Python vérifie que la bibliothèque
peut être importée.

Le paramètre changed_when: false indique que cette
vérification ne constitue pas une modification.

Résultat observé :

```text
Version PyModbus installee : 3.16.1
```

## 6. Vérification syntaxique du playbook

Depuis ctrl :

```bash
cd /vagrant/ansible
```

Commande :

```bash
ansible-playbook -i inventory.ini playbooks/07_preparation_simulation_python.yml --syntax-check
```

Résultat :

Vérification syntaxique réussie.

Aucune erreur YAML ou Ansible n'a été signalée.

## 7. Première exécution du playbook

Depuis ctrl :

```bash
cd /vagrant/ansible
ansible-playbook -i inventory.ini playbooks/07_preparation_simulation_python.yml
```

Résultat :

```text
PLAY RECAP

ctrl : ok=9 changed=0 unreachable=0 failed=0
```

Toutes les tâches ont été exécutées avec succès.

Aucune modification n'a été nécessaire, car les
dépendances étaient déjà installées pendant la phase 06.

## 8. Vérification de l'idempotence

Le playbook a été exécuté une deuxième fois.

Commande :

```bash
ansible-playbook -i inventory.ini playbooks/07_preparation_simulation_python.yml
```

Résultat :

```text
PLAY RECAP

ctrl : ok=9 changed=0 unreachable=0 failed=0
```

Comparaison :

| Indicateur | Première exécution | Deuxième exécution |
|---|---:|---:|
| OK | 9 | 9 |
| CHANGED | 0 | 0 |
| FAILED | 0 | 0 |
| UNREACHABLE | 0 | 0 |

L'idempotence a été confirmée dans l'environnement existant.

Le playbook peut être rejoué sans provoquer de
modifications inutiles lorsque la configuration
attendue est déjà présente.

La reproductibilité sur une VM entièrement neuve
reste à vérifier ultérieurement.

## 9. Test fonctionnel du simulateur

Après l'exécution du playbook, un test fonctionnel
a été réalisé depuis ctrl.

### Activation de l'environnement

```bash
source /home/vagrant/venv-simulation-ot/bin/activate
```

### Lancement

```bash
cd /vagrant/simulation
python simulateur_cuve.py
```

### Résultats observés

Connexion Modbus TCP réussie vers :

192.168.75.135:5020

Le simulateur a transmis le niveau de la cuve
et lu l'état de la pompe.

Extrait :

```text
[14:49:42] Connexion Modbus TCP etablie.
[14:49:42] Niveau : 21.0 % | Pompe : ON | Variation : +1.0 %/s
[14:49:52] Niveau : 29.0 % | Pompe : ON | Variation : +1.0 %/s
[14:50:09] Niveau : 43.0 % | Pompe : ON | Variation : +1.0 %/s
```

Le niveau de la cuve a progressé de 21 % à 43 %
avec la pompe en fonctionnement.

Le test confirme que la communication Modbus TCP
reste fonctionnelle après l'automatisation Ansible.

Ce test n'a pas couvert un nouveau franchissement
du seuil haut de 80 %.

### Arrêt du simulateur

Le simulateur a été interrompu avec Ctrl+C.

Messages observés :

```text
Arret demande par l'utilisateur.
Connexion Modbus fermee.
```

L'arrêt du programme et la fermeture de la connexion
Modbus se sont effectués correctement.

## 10. Principes d'idempotence

Plusieurs mécanismes contribuent à l'idempotence.

### Module apt

Le paramètre state: present évite de réinstaller
les paquets déjà présents.

### Paramètre creates

Le module command ne recrée pas l'environnement
virtuel lorsque son exécutable Python existe déjà.

### Module pip

Les dépendances sont vérifiées par rapport au
fichier requirements.txt.

### Paramètre changed_when

Les commandes de consultation sont déclarées
sans modification d'état.

Ces mécanismes permettent de maintenir une
configuration cohérente lors des exécutions successives.

## 11. Limites actuelles

L'automatisation concerne uniquement la préparation
de l'environnement Python sur ctrl.

Les éléments suivants ne sont pas encore automatisés :

- Démarrage et arrêt du simulateur.
- Exécution en tant que service systemd.
- Reconnexion automatique après une coupure Modbus.
- Configuration externe des paramètres de simulation.
- Déploiement du simulateur sur une VM industrielle dédiée.
- Filtrage des communications Modbus TCP.
- Collecte et historisation des données industrielles.

Le simulateur est volontairement lancé manuellement
pour conserver le contrôle des tests.

## 12. Évolutions prévues

Les prochaines évolutions du laboratoire comprennent :

- Amélioration de la robustesse du simulateur Python.
- Paramétrage externe des adresses et des débits.
- Simulation de défaillances industrielles.
- Segmentation des réseaux IT et OT.
- Sécurisation des communications industrielles.
- Intégration de Docker et Docker Compose.
- Collecte de données avec InfluxDB.
- Visualisation industrielle avec Grafana.
- Analyse du trafic OT avec des outils de cybersécurité.

Ces évolutions feront l'objet de phases distinctes.

## 13. Résultat de la phase

L'environnement Python du simulateur industriel
est désormais préparé et vérifié automatiquement
à l'aide d'Ansible.

Le playbook a été exécuté deux fois avec succès.

Résultat :

ok=9 changed=0 failed=0

L'idempotence a été vérifiée sur la VM ctrl existante.

Un test fonctionnel a confirmé que le simulateur communique toujours avec OpenPLC via Modbus TCP.

Cette phase améliore la reproductibilité et la maintenabilité du laboratoire IaC OT, sans modifier la logique de commande industrielle.
