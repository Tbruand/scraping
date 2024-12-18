from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup
import re
import pandas as pd
import os
import json
from dotenv import load_dotenv
from datetime import datetime


class SeleniumScraper:
    def __init__(self):
        # Charger les variables d'environnement depuis le fichier .env
        env_path = os.path.join(os.path.dirname(__file__), "../../.env")
        load_dotenv(env_path)

        # Récupérer l'URL de la variable d'environnement
        self.url = os.getenv("MY_URL")
        if not self.url:
            print("La variable d'environnement 'MY_URL' n'est pas définie.")
        else:
            print("L'URL est :", self.url)

        # Configurer Selenium
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Mode sans interface graphique
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(service=Service(), options=chrome_options)

    def handle_cookies(self):
        """Gère la bannière des cookies en la supprimant du DOM."""
        try:
            # Attendre que la balise soit présente dans le DOM
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "pe-cookies"))
            )
            # Exécuter JavaScript pour supprimer la balise des cookies
            self.driver.execute_script("""
                let cookieBanner = document.querySelector('pe-cookies');
                if (cookieBanner) {
                    cookieBanner.remove();
                }
            """)
            print("Bannière des cookies supprimée avec succès.")
        except TimeoutException:
            print("Bannière des cookies introuvable ou déjà supprimée.")
        except Exception as e:
            print(f"Erreur lors de la suppression de la bannière des cookies : {e}")


    def fetch_data(self):
        if not self.url:
            return None

        try:
            self.driver.get(self.url)

            # Gérer les cookies
            self.handle_cookies()

            print("Chargement des premiers éléments...")

            # Scraper les 20 premiers éléments initialement chargés
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h2[data-intitule-offre]"))
            )
            total_elements = len(self.driver.find_elements(By.CSS_SELECTOR, "h2[data-intitule-offre]"))
            print(f"{total_elements} éléments initiaux récupérés.")

            # Boucle pour cliquer sur le bouton et charger plus d'annonces
            while True:
                print("Chargement des données avec le bouton 'Charger plus'...")

                # Essayer de cliquer sur le bouton "Charger plus"
                try:
                    load_more_button = self.driver.find_element(By.CSS_SELECTOR, ".btn.btn-primary")
                    if load_more_button.is_displayed() and load_more_button.is_enabled():
                        load_more_button.click()

                        # Attendre que de nouveaux éléments soient chargés
                        WebDriverWait(self.driver, 10).until(
                            lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "h2[data-intitule-offre]")) > total_elements
                        )
                        # Mettre à jour le nombre total d'éléments
                        total_elements = len(self.driver.find_elements(By.CSS_SELECTOR, "h2[data-intitule-offre]"))
                        print(f"{total_elements} éléments chargés au total.")
                    else:
                        print("Le bouton 'Charger plus' n'est pas cliquable.")
                        break
                except NoSuchElementException:
                    print("Bouton 'Charger plus' introuvable. Fin de la pagination.")
                    break
                except TimeoutException:
                    print("Timeout lors du chargement des nouveaux éléments.")
                    break

            # Récupérer le contenu HTML final après avoir chargé toutes les annonces
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            return soup
        except Exception as e:
            print(f"Erreur lors de la récupération des données : {e}")
            return None

    def recup_data(self, soup):
        annuaire = []
        offres = soup.find_all('h2', attrs={'data-intitule-offre': True})
        for offre in offres:
            try:
                data_intitule_offre = offre.get('data-intitule-offre')
                titre = offre.find('span', class_='media-heading-title').text.strip()
                # Nettoyer le titre
                titre = re.split(r"\s+[FH]/H\s*", titre, maxsplit=1)[0].strip()
                # Ajouter dans la liste
                annuaire.append({
                    "id_url": data_intitule_offre,
                    "title": titre
                })
            except Exception as e:
                print(f"Erreur lors de l'extraction d'une offre : {e}")
        return annuaire

    def save_to_json(self, data, filename="extracted_data.json", folder="data/raw"):
        try:
            os.makedirs(folder, exist_ok=True)
            base_name, extension = os.path.splitext(filename)
            filepath = os.path.join(folder, filename)
            i = 1
            while os.path.exists(filepath):
                filepath = os.path.join(folder, f"{base_name}({i}){extension}")
                i += 1
            with open(filepath, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            print(f"Données enregistrées dans le fichier : {filepath}")
        except Exception as e:
            print(f"Erreur lors de l'enregistrement du fichier JSON : {e}")

    def close_driver(self):
        self.driver.quit()


if __name__ == "__main__":
    scraper = SeleniumScraper()
    try:
        # Charger et extraire les données
        soup = scraper.fetch_data()
        if soup:
            data = scraper.recup_data(soup)
            print(f"Nombre total d'annonces récupérées : {len(data)}")

            # Enregistrer les données dans un fichier JSON
            scraper.save_to_json(data)
    finally:
        scraper.close_driver()