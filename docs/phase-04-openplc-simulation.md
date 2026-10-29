# Phase 04 — Préparation OT-PROCESS et première logique OpenPLC

> **Projet :** Labo IaC OT  
> **Statut :** préparation d'`ot-process` validée ; OpenPLC Runtime v4 installé et accessible ; programme Ladder testé **dans le simulateur local d'OpenPLC Editor**. Déploiement du programme sur `ot-process`, simulation physique Python et Modbus TCP : **à réaliser**.

## 1. Objectifs pédagogiques

Cette phase illustre comment préparer un nœud industriel simulé à l'aide d'Ansible, installer un environnement d'exécution d'automate, programmer une commande de pompe en Ladder (IEC 61131-3) et vérifier son comportement. Les notions étudiées sont :

- gestion de dépendances Ubuntu et automatisation idempotente ;
- distinction entre OpenPLC **Editor** (conception) et **Runtime** (exécution) ;
- variables `REAL`/`BOOL`, comparateurs `LE`/`GE`, contacts NO/NC et bobine ;
- auto-maintien et régulation par **hystérésis** ;
- tests avec valeurs forcées, interprétation du débogueur et diagnostic d'incident ;
- exposition des services, privilèges, versionnement et reproductibilité.

L'objectif métier est un procédé virtuel de **station de pompage** dont le niveau de cuve déterminera l'état de la pompe. Un simulateur Python reproduira ultérieurement la physique du procédé et échangera des données avec l'automate par Modbus TCP.

## 2. Architecture et périmètre réel

| Élément | Rôle | État au terme de cette séquence |
|---|---|---|
| Windows 11 / VMware Workstation 25 | Hôte des VM ; OpenPLC Editor 4.3.3 | Éditeur installé, simulation Ladder testée |
| `ctrl` | Nœud Ansible | Fonctionnel |
| `ot-process` | Nœud de procédé industriel simulé | Ubuntu et OpenPLC Runtime installés |
| `ot-supervision` | SCADA, collecte, InfluxDB, Grafana | VM non créée à ce stade |
| `fw-ot` | Futur routage et filtrage interzones | VM non créée à ce stade |
| `monitor` | Future surveillance réseau | VM non créée à ce stade |

Réseaux pertinents :

| Réseau | Sous-réseau | Adresse connue | Usage |
|---|---|---|---|
| VMnet2 — gestion | `192.168.56.0/24` | `ctrl` : `192.168.56.10` | Gestion du labo |
| VMnet3 — process | `192.168.100.0/24` | `ot-process` : `192.168.100.10` | Procédé industriel |
| VMnet4 — supervision | `192.168.110.0/24` | `ot-supervision` : `192.168.110.10` (prévue) | Future supervision |
| VMnet8 — NAT | `192.168.75.0/24` | `ctrl` : `192.168.75.134` ; `ot-process` : `192.168.75.135` ; Windows : `192.168.75.1` | Accès temporaire pour administration et installation |

**Attention :** VMnet8 permet actuellement des accès directs temporaires. Il ne prouve pas que la segmentation finale est opérationnelle. Ce laboratoire est distinct du projet **OTLAB2**.

Le dépôt versionné se trouve sous Windows dans `D:\Labo-IaC-OT\projet` et est partagé dans `ctrl` via `/vagrant`. Le dépôt public est [YGregCls/labo-iac-ot](https://github.com/YGregCls/labo-iac-ot).

## 3. Contrôles avant installation

Depuis `ctrl`, dans `/vagrant/ansible`, l'inventaire `inventory.ini` cible le groupe `process`, contenant `ot-process`. L'accès Ansible repose sur SSH et une clé Ed25519.

Une nouvelle session SSH ne retrouvait pas son agent :

```text
Could not open a connection to your authentication agent.
```

L'agent a été démarré et la clé chargée :

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519_ansible
ssh-add -l
```

Le dernier contrôle a présenté la clé `ansible-ctrl-iac-ot (ED25519)`. **Ne jamais transmettre la phrase secrète ou publier la clé privée.**

Contrôles distants exécutés :

```bash
ansible process -i inventory.ini -a "python3 --version"
ansible process -i inventory.ini -b -m command -a "dpkg --audit"
ansible process -i inventory.ini -b -m ansible.builtin.apt -a "update_cache=yes cache_valid_time=3600"
```

Résultats : Python `3.12.3`, aucun paquet anormal signalé par `dpkg --audit`. Le cache APT était considéré valide (`cache_updated=false`, `changed=false`) ; **ce seul retour ne prouve pas une nouvelle connexion aux dépôts**.

Inventaire initial avec `command -v` : `git`, `curl`, `wget` présents ; `gcc`, `g++`, `make`, `cmake`, `pip3` absents.

### Lecture des statuts Ansible

- `rc=0` : la commande s'est terminée avec succès.
- `failed=0`, `unreachable=0` : aucune erreur ni inaccessibilité déclarée.
- `CHANGED` peut apparaître pour une commande de **lecture** avec `command` ou `shell` ; cela ne prouve pas qu'un fichier a été modifié.
- `changed=0` lors d'une seconde exécution d'un playbook de configuration démontre que l'état demandé est déjà satisfait dans ce contexte.

## 4. Automatisation de la préparation de base

### `ansible/playbooks/04_preparation_ot_process.yml`

Le playbook utilise `ansible.builtin.apt` avec `state: present`, `update_cache: true` et `cache_valid_time: 3600` pour assurer la présence de :

```yaml
git
curl
wget
build-essential
cmake
python3-pip
python3-venv
```

`build-essential` fournit notamment GCC, G++ et Make. `python3-venv` autorise la création d'environnements Python isolés ; il est préférable d'y installer les bibliothèques de simulation plutôt que de modifier l'environnement Python système.

Commandes de validation :

```bash
cd /vagrant/ansible
ansible-playbook -i inventory.ini playbooks/04_preparation_ot_process.yml --syntax-check
ansible-playbook -i inventory.ini playbooks/04_preparation_ot_process.yml --check
ansible-playbook -i inventory.ini playbooks/04_preparation_ot_process.yml
ansible-playbook -i inventory.ini playbooks/04_preparation_ot_process.yml
```

| Étape | Résultat observé |
|---|---|
| Contrôle syntaxique | Réussi |
| Simulation `--check` | `ok=2 changed=1 failed=0` |
| Première exécution réelle | `ok=2 changed=1 failed=0` |
| Deuxième exécution réelle | `ok=2 changed=0` : **idempotence validée** |

Versions vérifiées à distance : GCC et G++ `13.3.0`, GNU Make `4.3`, CMake `3.28.3`, pip `24.0` pour Python `3.12`.

## 5. OpenPLC Runtime v4 sur `ot-process`

### 5.1 Choix de version

OpenPLC Runtime v3 est en fin de maintenance ; le laboratoire utilise v4. Le code source a été figé à la révision :

```text
8d69d935a7915bef9b67bbea46cf87c68d112246
```

Sources : [dépôt officiel OpenPLC Runtime](https://github.com/Autonomy-Logic/openplc-runtime) et [présentation officielle](https://autonomylogic.com/products/runtime).

Le playbook `ansible/playbooks/05_recuperation_openplc.yml` emploie `ansible.builtin.git` avec :

```yaml
repo: https://github.com/Autonomy-Logic/openplc-runtime.git
dest: /opt/openplc-runtime
version: "8d69d935a7915bef9b67bbea46cf87c68d112246"
update: false
```

La syntaxe et l'exécution ont été validées (`ok=2 changed=1`). La révision a été confirmée par :

```bash
ansible process -i inventory.ini -b -m command -a "git -C /opt/openplc-runtime rev-parse HEAD"
```

### 5.2 Incident Git « dubious ownership »

Sans `-b`, Git a renvoyé :

```text
fatal: detected dubious ownership in repository at '/opt/openplc-runtime'
```

**Cause :** le dépôt avait été créé avec `become: true` et appartenait à `root`, mais le contrôle était exécuté par `vagrant`. **Correction :** refaire la vérification avec `-b`, sans contourner le contrôle `safe.directory` de Git.

### 5.3 Inspection avant exécution du script

Le fichier `/opt/openplc-runtime/install.sh` a été inspecté avant exécution. Points relevés :

- exige les privilèges `root` sous Linux ;
- utilise `systemd` pour créer et activer `openplc-runtime.service`, configuré `User=root` et `Restart=always` ;
- prépare un environnement virtuel Python `venvs/runtime` ;
- peut installer des paquets APT et télécharger des composants supplémentaires, dont CMake ;
- applique des permissions à certains répertoires, dont `/var/run/runtime` ;
- **mode Docker par défaut** ; l'option `--native` déclenche la compilation native.

Ces choix imposent une analyse de privilèges, de provenance des dépendances et de surface d'exposition. Le script a été utilisé pour ce labo de simulation ; il n'est pas présenté comme une configuration durcie pour la production.

### 5.4 Ressources et snapshot

Avant installation : Ubuntu `24.04.3 LTS`, 1,9 Gio de RAM (environ 1,5 Gio disponibles), 2,9 Gio de swap, 24 Gio libres sur la partition principale. Un snapshot VMware `PHASE-04-AVANT-OPENPLC` a été créé sur `ot-process`.

### 5.5 Installation native

Le playbook `ansible/playbooks/06_installation_openplc.yml` appelle :

```yaml
ansible.builtin.command:
  argv:
    - ./install.sh
    - --native
  chdir: /opt/openplc-runtime
  creates: /opt/openplc-runtime/.installed
async: 3600
poll: 15
```

Le marqueur `.installed` évite une nouvelle installation si le fichier existe ; **il ne vérifie pas à lui seul la santé du Runtime**. Le suivi asynchrone a affiché `started=True finished=False` pendant la compilation, puis le playbook s'est terminé avec `ok=2 changed=1`.

### 5.6 Vérification du service et du réseau

```bash
ansible process -i inventory.ini -b -m command -a "systemctl is-active openplc-runtime.service"
ansible process -i inventory.ini -b -m command -a "ss -lntp"
```

Le service a été confirmé actif. `ss` a montré un processus `python3` en écoute sur **`0.0.0.0:8443`**, ce qui signifie toutes les interfaces IPv4 de la VM ; le port SSH `22` était également en écoute. Le port Modbus `502` n'était **pas encore observé**.

Depuis PowerShell Windows :

```powershell
Test-NetConnection 192.168.75.135 -Port 8443
```

Résultat : `TcpTestSucceeded : True`, avec `SourceAddress : 192.168.75.1` via VMnet8. **Ce test démontre la connectivité TCP**, pas encore l'authentification ni le déploiement applicatif OpenPLC Editor → Runtime.

**Point de sécurité :** le Runtime écoutant sur `0.0.0.0`, il est potentiellement accessible aussi depuis l'interface NAT de la VM. Le filtrage interzones et la restriction des chemins d'administration restent à réaliser. Ne pas ouvrir ces ports sur Internet.

## 6. OpenPLC Editor et projet automate

OpenPLC Editor `4.3.3` a été installé sur Windows 11. Un projet de type **PLC Project**, nommé `Station_Pompage_OT`, a été créé dans le périmètre du projet local. Langage : **Ladder Diagram (LD)**. Tâche cyclique : **`T#20ms`**, soit une fréquence nominale de 50 cycles/s ; cette valeur ne garantit pas un temps réel strict.

L'éditeur local permet de concevoir et déboguer un programme sans que celui-ci ait déjà été transféré au Runtime de la VM. Les captures de tests décrites ci-dessous proviennent **du débogueur local de l'éditeur Windows**.

### 6.1 Dictionnaire des variables

Toutes les variables sont actuellement de classe `Local`, sans adresse matérielle ou Modbus affectée.

| Variable | Type | Valeur initiale | Fonction |
|---|---|---|---|
| `Niveau_Cuve` | `REAL` | `50.0` | Niveau simulé de la cuve, en % |
| `Pompe_Marche` | `BOOL` | `FALSE` | Commande logique de la pompe |
| `Seuil_Bas` | `REAL` | `30.0` | Seuil de démarrage |
| `Seuil_Haut` | `REAL` | `80.0` | Seuil d'arrêt |
| `Demande_Demarrage` | `BOOL` | `FALSE` | Résultat du comparateur de niveau bas |
| `Demande_Arret` | `BOOL` | `FALSE` | Résultat du comparateur de niveau haut |

Un `REAL` représente une valeur décimale ; un `BOOL` représente `TRUE`/`FALSE`. `Niveau_Cuve` est pour l'instant alimenté manuellement par le débogueur : ce n'est **pas encore** une mesure fournie par un simulateur Python.

### 6.2 Réseau 1 — Détection du niveau bas

Bloc `LE` (*less or equal*) avec `Execution Control` activé :

```text
IN1 = Niveau_Cuve
IN2 = Seuil_Bas
OUT = Demande_Demarrage
```

Formule : `Demande_Demarrage := (Niveau_Cuve <= Seuil_Bas)`.

L'activation du contrôle d'exécution a séparé l'entrée booléenne `EN` des entrées numériques `IN1` et `IN2`. `ENO` reflète l'activation du bloc ; **ce n'est pas le résultat de la comparaison**. Le résultat est `OUT`.

### 6.3 Réseau 2 — Détection du niveau haut

Bloc `GE` (*greater or equal*) :

```text
IN1 = Niveau_Cuve
IN2 = Seuil_Haut
OUT = Demande_Arret
```

Formule : `Demande_Arret := (Niveau_Cuve >= Seuil_Haut)`.

### 6.4 Réseau 3 — Commande avec auto-maintien

- Contact normalement ouvert `Demande_Demarrage`.
- Contact normalement ouvert `Pompe_Marche` **en parallèle** : maintien lorsque la demande de démarrage disparaît.
- Contact normalement fermé, ou `Negated`, `Demande_Arret` **en série après la jonction** : coupe les deux branches si le niveau haut est atteint.
- Bobine normale `Pompe_Marche` en sortie.

Expression logique :

```text
Pompe_Marche := (Demande_Demarrage OR Pompe_Marche) AND NOT Demande_Arret
```

Ce montage utilise l'état précédent de `Pompe_Marche` comme mémoire de commande (*auto-maintien*). Il n'est pas un circuit de sécurité câblé et ne remplace aucune fonction de sécurité réelle.

## 7. Pourquoi l'hystérésis ?

Avec un seuil unique, une mesure légèrement fluctuante pourrait commander des démarrages et arrêts répétés de la pompe. Cela provoquerait du **pompage logique** (*chattering*) et, sur une installation réelle, pourrait solliciter inutilement moteurs et contacteurs.

Deux seuils distincts créent une bande d'hystérésis :

- **à 30 % ou moins :** démarrer la pompe ;
- **de 30 % à 80 % :** conserver l'état précédent ;
- **à 80 % ou plus :** arrêter la pompe.

La bande mesure ici `80 - 30 = 50` points de pourcentage. Ces seuils sont **pédagogiques**, non dimensionnés pour un réservoir réel. En exploitation, ils dépendraient du volume, du débit, de la fréquence admissible de démarrage, des capteurs et de l'analyse de risques.

| Niveau | Pompe initialement arrêtée | Pompe déjà en marche |
|---|---|---|
| 20 % | Démarre | Reste en marche |
| 50 % | Reste arrêtée | Reste en marche |
| 90 % | Reste arrêtée | S'arrête |

La commande cyclique répète l'évaluation à chaque cycle de tâche. Le choix `T#20ms` est sans rapport direct avec la vitesse physique d'évolution du niveau, qui sera simulée séparément.

## 8. Tests locaux dans OpenPLC Editor

Après génération/compilation du projet, le débogueur a permis de surveiller des variables. `Force Value` a été utilisé **uniquement dans la simulation pédagogique locale**, pas sur un équipement industriel réel.

| Scénario | Action et état initial | Résultat observé | Verdict |
|---|---|---|---|
| Démarrage niveau bas | Forçage `Niveau_Cuve = 25.0`, pompe initialement arrêtée | `Pompe_Marche = TRUE` | **Validé** |
| Maintien en marche | Passage de 25 % à 50 % | `Pompe_Marche` reste `TRUE` | **Validé** |
| Arrêt niveau haut après recompilation | Forçage direct à 90 % | `Demande_Arret = TRUE` ; `Pompe_Marche = FALSE` | **Validé** |
| Seuil haut inclusif | Forçage à 80 % | `Demande_Arret = TRUE` ; `Pompe_Marche = FALSE` | **Validé** |
| Maintien à l'arrêt | Passage de 80 % à 50 % | `Pompe_Marche` reste `FALSE` | **Confirmé par l'utilisateur** |

### Incident rencontré : arrêt non déclenché au premier essai

Lors d'une première session de simulation, à 80 % puis 90 %, les valeurs observées étaient `Demande_Arret = FALSE` et `Pompe_Marche = TRUE`, malgré un bloc `GE` visuellement correct. Le programme montrait par moments un `*` devant `main`, indiquant des modifications non sauvegardées.

**Procédure suivie :** arrêter le débogage, enregistrer `main` avec `Ctrl + S`, vérifier la disparition du `*`, puis relancer la compilation et le simulateur. Après cette opération, `Demande_Arret` a correctement pris `TRUE` à 90 % et 80 %, avec pompe à `FALSE`.

**Diagnostic prudent :** une version compilée antérieure est une explication plausible, **mais non démontrée de façon formelle**. Ne pas présenter cette hypothèse comme une certitude. La procédure et les résultats sont reproductibles et doivent être conservés dans le retour d'expérience.

### Limites de ces tests

Les tests confirment la logique sur des valeurs forcées, pas encore le débit d'une pompe, la dynamique d'une cuve, une liaison Modbus ni le fonctionnement du programme sur `ot-process`. Aucun équipement physique n'a été commandé.

## 9. Bonnes pratiques de cybersécurité OT

1. **Limiter les accès :** le port d'administration TCP 8443 ne doit être accessible que depuis les postes et zones autorisés.
2. **Segmenter réellement :** ne considérer la séparation Process/Supervision comme effective qu'après déploiement et tests de règles sur `fw-ot`.
3. **Ne pas exposer Modbus TCP à Internet :** Modbus classique n'apporte pas, à lui seul, l'authentification et le chiffrement nécessaires.
4. **Limiter les privilèges :** analyser l'exécution du service OpenPLC sous `root` et les permissions des répertoires.
5. **Contrôler la chaîne logicielle :** épingler les révisions Git, examiner les scripts privilégiés et les dépendances téléchargées.
6. **Séparer commande et sécurité :** la régulation Ladder n'est pas un arrêt d'urgence ou une fonction de sûreté certifiée.
7. **Prévoir les défauts :** perte de mesure, dépassement de seuil, blocage de pompe, redémarrage et communications indisponibles seront étudiés dans les scénarios futurs.
8. **Ne jamais publier** les clés privées SSH, secrets, mots de passe ou configurations sensibles.

## 10. Reproductibilité et gestion de versions

Fichiers locaux créés pendant cette phase :

```text
ansible/playbooks/04_preparation_ot_process.yml
ansible/playbooks/05_recuperation_openplc.yml
ansible/playbooks/06_installation_openplc.yml
openplc/Station_Pompage_OT/  # projet local : vérifier le chemin exact avant ajout
docs/phase-04-openplc-simulation.md
```

Le dépôt Git ne doit pas contenir les répertoires générés de VMware, les clés SSH, des fichiers de cache ou des artefacts volumineux sans intérêt de reproduction. Vérifier la structure et les fichiers générés par OpenPLC Editor avant `git add`.

Une fois les fichiers placés et contrôlés dans le dépôt Windows :

```powershell
cd D:\Labo-IaC-OT\projet
git status -sb
git add docs/phase-04-openplc-simulation.md ansible/playbooks/04_preparation_ot_process.yml ansible/playbooks/05_recuperation_openplc.yml ansible/playbooks/06_installation_openplc.yml
git status -sb
git commit -m "docs: document phase 04 OpenPLC et tests Ladder"
git push origin main
```

**Le projet OpenPLC sera ajouté dans un commit contrôlé après vérification de son emplacement exact et de ses fichiers.** Ne pas considérer ces commandes comme déjà exécutées.

