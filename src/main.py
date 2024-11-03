# import package
import requests
import re
import pandas as pd
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from datetime import datetime

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer l'URL de la variable d'environnement
url = os.getenv('MY_URL')

# Vérifier si l'URL a été récupérée avec succès
if url is not None:
    print("L'URL est :", url)
else:
    print("La variable d'environnement 'MY_URL' n'est pas définie.")

    
path = ".\\scraping\\results_scrap\\"
# dico qui regroupe les noms, adresses et telephone
annuaire = {}
# recupere la date
today = datetime.now()
# format de la date dd_mm_YY
f_date = today.strftime("%d_%m_%Y-(%Hh%M)")

# import le code de la page
response = requests.get(url)
# recupere au format html
soup = BeautifulSoup(response.text, "html.parser")


# cherche les nom, addresse et telephone sur la page
name = soup.find_all("h3", class_="nom-prenom")
addresses = soup.find_all("span", class_="adresse")
phone = soup.find_all("span", class_="telephone")

# recupere le text des noms, adresses et telephones
texte_name = [item.get_text(strip=True) for item in name]
addresses_liste = [re.sub(r'\s+', ' ', address.get_text(strip=True)) for address in addresses]
texte_phone = [item.get_text(strip=True) for item in phone]

# rempli le dictionnaire annuaire sous forme de listes
annuaire = {
    "nom": [],
    "adresse": [],
    "telephone": []
}

# rempli les listes avec les donnees extraites
for i in range(len(texte_name)):
    annuaire["nom"].append(texte_name[i] if i < len(texte_name) else None)
    annuaire["adresse"].append(addresses_liste[i] if i < len(addresses_liste) else None)
    annuaire["telephone"].append(texte_phone[i] if i < len(texte_phone) else None)

# convertir le dico en DataFrame
df = pd.DataFrame(annuaire)
df.head()
# export en csv
df.to_csv(f"{path}scrap_{f_date}", index=False, encoding="utf-8")
