
import time
from datetime import datetime

from pymodbus.client import ModbusTcpClient


# ============================================================
# SIMULATION D'UNE STATION DE POMPAGE
# ============================================================

# Connexion au serveur OpenPLC
PLC_IP = "192.168.75.135"
PLC_PORT = 5020
DEVICE_ID = 1

# Adresses Modbus
REGISTRE_NIVEAU = 0
COIL_POMPE = 0

# Paramètres physiques de notre simulation
NIVEAU_INITIAL = 20.0
DEBIT_POMPE = 2.0
CONSOMMATION_EAU = 1.0
INTERVALLE = 1.0

NIVEAU_MIN = 0.0
NIVEAU_MAX = 100.0


def afficher(message):
    """Affiche un message avec l'heure."""
    heure = datetime.now().strftime("%H:%M:%S")
    print(f"[{heure}] {message}", flush=True)


def envoyer_niveau(client, niveau):
    """Transmet le niveau de la cuve à OpenPLC."""

    valeur = int(round(niveau))

    reponse = client.write_register(
        address=REGISTRE_NIVEAU,
        value=valeur,
        device_id=DEVICE_ID,
    )

    if reponse.isError():
        raise RuntimeError(f"Erreur d'écriture Modbus : {reponse}")


def lire_pompe(client):
    """Lit l'état de la pompe calculé par OpenPLC."""

    reponse = client.read_coils(
        address=COIL_POMPE,
        count=1,
        device_id=DEVICE_ID,
    )

    if reponse.isError():
        raise RuntimeError(f"Erreur de lecture Modbus : {reponse}")

    return bool(reponse.bits[0])


def simuler():
    """Exécute la simulation de la station de pompage."""

    niveau = NIVEAU_INITIAL

    client = ModbusTcpClient(
        host=PLC_IP,
        port=PLC_PORT,
        timeout=3,
    )

    afficher("Démarrage du simulateur industriel")
    afficher(f"Automate OpenPLC : {PLC_IP}:{PLC_PORT}")

    try:
        if not client.connect():
            afficher("ERREUR : impossible de joindre OpenPLC")
            return

        afficher("Connexion Modbus TCP établie")

        # Première transmission du niveau à l'automate
        envoyer_niveau(client, niveau)

        while True:
            # Laisser un court instant à OpenPLC
            # pour traiter le nouveau niveau
            time.sleep(0.2)

            # Lire la décision de l'automate
            pompe_marche = lire_pompe(client)

            # Simuler le comportement physique de la cuve
            variation = -CONSOMMATION_EAU

            if pompe_marche:
                variation += DEBIT_POMPE

            niveau += variation * INTERVALLE

            # Empêcher le niveau de dépasser les limites
            niveau = max(NIVEAU_MIN, min(NIVEAU_MAX, niveau))

            # Envoyer le nouveau niveau à OpenPLC
            envoyer_niveau(client, niveau)

            etat = "ON " if pompe_marche else "OFF"
            afficher(
                f"Niveau : {niveau:5.1f} % | "
                f"Pompe : {etat} | "
                f"Variation : {variation:+.1f} %/s"
            )

            time.sleep(INTERVALLE)

    except KeyboardInterrupt:
        afficher("Arrêt demandé par l'utilisateur")

    except Exception as erreur:
        afficher(f"ERREUR : {erreur}")

    finally:
        client.close()
        afficher("Connexion Modbus fermée")


if __name__ == "__main__":
    simuler()
