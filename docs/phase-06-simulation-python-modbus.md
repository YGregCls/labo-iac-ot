
# Phase 06 — Simulation industrielle Python et Modbus TCP

## 1. Objectif

Cette phase a pour objectif d'intégrer une simulation dynamique
d'un procédé industriel au laboratoire IaC OT.

Le procédé retenu est une station de pompage permettant de maintenir
le niveau d'eau d'une cuve entre deux seuils.

L'architecture repose sur deux composants :

- OpenPLC Runtime v4 : exécution de la logique de commande industrielle.
- Python : simulation du comportement physique de la cuve.

Les échanges entre ces composants utilisent le protocole Modbus TCP.

L'objectif est de conserver une séparation entre la logique de commande
de l'automate et la simulation du procédé physique.

## 2. Architecture technique

### Machine de contrôle

Nom : ctrl

Système : Ubuntu 24.04

Rôle :
- Administration du laboratoire.
- Exécution d'Ansible.
- Hébergement initial du simulateur Python.
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

### Précision sur le réseau

Pendant cette première étape, le simulateur Python exécuté sur ctrl
communique avec OpenPLC par le réseau NAT.

Adresse de connexion :
192.168.75.135:5020

L'objectif à terme est de placer le simulateur sur le réseau industriel
192.168.100.0/24 et de limiter les accès Modbus à ce réseau.

## 3. Principe de fonctionnement

Le programme Python simule le niveau d'eau d'une cuve.

OpenPLC exécute la logique de commande de la pompe.

Les seuils configurés sont :

- Seuil bas : 30 %
- Seuil haut : 80 %

Fonctionnement attendu :

1. Le niveau de la cuve diminue lorsque la pompe est arrêtée.
2. À 30 % ou moins, OpenPLC commande le démarrage de la pompe.
3. Lorsque la pompe fonctionne, le niveau augmente.
4. À 80 % ou plus, OpenPLC commande l'arrêt de la pompe.
5. Le cycle recommence.

Entre les seuils, la commande de la pompe conserve son état précédent.

Cette logique est appelée hystérésis.

## 4. Configuration du programme OpenPLC

Projet :
Station_Pompage_OT

Langage :
Ladder Diagram (LD)

Le programme contient quatre réseaux.

### Réseau 1 — Conversion du niveau

Fonction :
TO_REAL

Entrée :
Niveau_Cuve_Modbus

Sortie :
Niveau_Cuve

Objectif :
Convertir le niveau entier reçu par Modbus en nombre réel.

### Réseau 2 — Détection du seuil bas

Fonction :
LE

Condition :
Niveau_Cuve <= Seuil_Bas

Sortie :
Demande_Demarrage

### Réseau 3 — Détection du seuil haut

Fonction :
GE

Condition :
Niveau_Cuve >= Seuil_Haut

Sortie :
Demande_Arret

### Réseau 4 — Commande de la pompe

Le quatrième réseau contient la logique de commande avec mémorisation.

La pompe démarre lorsque la demande de démarrage est active.

Elle reste en fonctionnement jusqu'à l'activation de la demande d'arrêt.

## 5. Variables utilisées

| Variable | Type | Adresse IEC | Fonction |
|---|---|---|---|
| Niveau_Cuve_Modbus | INT | %MW0 | Niveau reçu via Modbus |
| Niveau_Cuve | REAL | — | Niveau utilisé par le Ladder |
| Pompe_Marche | BOOL | %QX0.0 | État de commande de la pompe |
| Seuil_Bas | REAL | — | Seuil de démarrage |
| Seuil_Haut | REAL | — | Seuil d'arrêt |
| Demande_Demarrage | BOOL | — | Condition de démarrage |
| Demande_Arret | BOOL | — | Condition d'arrêt |

## 6. Configuration du serveur Modbus TCP

Le serveur Modbus a été configuré depuis OpenPLC Editor.

Nom :
Modbus_TCP_OT

Protocole :
Modbus TCP

État :
Activé

Adresse d'écoute :
0.0.0.0

Port :
5020

### Buffer Mapping

| Zone | Nombre d'adresses exposées |
|---|---:|
| %QW | 0 |
| %MW | 1 |
| %MD | 0 |
| %ML | 0 |
| %QX | 1 |
| %MX | 0 |
| %IX | 0 |
| %IW | 0 |

Le fichier de configuration généré sur ot-process est :

/opt/openplc-runtime/core/src/drivers/plugins/python/modbus_slave/modbus_slave.json

Le déploiement OpenPLC a activé le plugin modbus_slave.

## 7. Vérification du serveur

La vérification a été effectuée depuis ctrl avec Ansible :

```bash
ansible process -i inventory.ini -b -m command -a "ss -lntp"
```

Résultat observé :

```text
0.0.0.0:5020 LISTEN
```

Le processus plc_main assure l'écoute du port Modbus TCP.

## 8. Environnement Python

Python :
3.12.3

Bibliothèque :
PyModbus 3.16.1

Environnement virtuel sur ctrl :

/home/vagrant/venv-simulation-ot

Création :

```bash
python3 -m venv /home/vagrant/venv-simulation-ot
```

Activation :

```bash
source /home/vagrant/venv-simulation-ot/bin/activate
```

Installation :

```bash
python -m pip install pymodbus==3.16.1
```

Le fichier simulation/requirements.txt permet de conserver
la dépendance Python nécessaire au projet.

## 9. Simulateur industriel

Fichier :

simulation/simulateur_cuve.py

### Responsabilités

Le simulateur Python :

- Établit une connexion Modbus TCP.
- Transmet le niveau de la cuve à OpenPLC.
- Lit l'état de la pompe.
- Calcule l'évolution du niveau d'eau.
- Répète ces opérations de manière cyclique.

Python ne décide pas directement du fonctionnement de la pompe.

Cette décision appartient au programme Ladder exécuté par OpenPLC.

### Paramètres de simulation

| Paramètre | Valeur |
|---|---:|
| Niveau initial | 20 % |
| Débit de la pompe | 2 %/s |
| Consommation | 1 %/s |
| Intervalle de simulation | 1 seconde |
| Niveau minimum | 0 % |
| Niveau maximum | 100 % |

Lorsque la pompe fonctionne, le niveau augmente théoriquement
de 1 % par seconde.

Lorsqu'elle est arrêtée, le niveau diminue théoriquement
de 1 % par seconde.

Ce modèle est pédagogique et ne représente pas une installation réelle.

## 10. Lancement du simulateur

Depuis ctrl :

```bash
source /home/vagrant/venv-simulation-ot/bin/activate
```

Puis :

```bash
cd /vagrant/simulation
```

Lancement :

```bash
python simulateur_cuve.py
```

Arrêt :

Ctrl + C

## 11. Tests réalisés

### Test 1 — Connexion TCP

Connexion à OpenPLC sur :

192.168.75.135:5020

Résultat :
Connexion réussie.

### Test 2 — Lecture Modbus

Lecture de l'état de Pompe_Marche.

Résultat :
Lecture réussie.

État initial observé :
True.

### Test 3 — Arrêt de la pompe

Écriture de la valeur 90 dans le registre Modbus d'adresse 0.

Résultat :
Écriture acceptée.

État de la pompe après traitement :
False.

### Test 4 — Démarrage de la pompe

Écriture de la valeur 20 dans le registre Modbus d'adresse 0.

Résultat :
Écriture acceptée.

État de la pompe après traitement :
True.

### Test 5 — Simulation dynamique

Le simulateur Python a été exécuté depuis ctrl.

Résultats observés :

- Connexion Modbus réussie.
- Évolution progressive du niveau d'eau.
- Lecture régulière de la commande de pompe.
- Écriture régulière du niveau dans OpenPLC.
- Arrêt de la pompe au seuil haut.

Extrait observé :

```text
[14:15:00] Niveau : 80.0 % | Pompe : ON
[14:15:01] Niveau : 79.0 % | Pompe : OFF
[14:15:02] Niveau : 78.0 % | Pompe : OFF
```

Le démarrage au seuil bas a été validé par un test manuel
d'écriture Modbus.

## 12. Limites actuelles

Le simulateur constitue une première version pédagogique.

Les améliorations prévues concernent :

- La gestion des coupures réseau.
- La reconnexion automatique.
- L'utilisation du temps réellement écoulé.
- La configuration externe des paramètres.
- La simulation de pannes et d'incidents industriels.
- L'automatisation du déploiement avec Ansible.
- La segmentation réseau et le filtrage du port Modbus.
- La collecte et la visualisation des données.

## 13. Résultat de la phase

Une première chaîne de simulation industrielle communicante
a été mise en place.

Les échanges Modbus TCP fonctionnent dans les deux sens.

OpenPLC conserve la responsabilité de la commande de la pompe.

Python assure la simulation du procédé physique.

