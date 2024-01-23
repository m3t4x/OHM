import requests
from bs4 import BeautifulSoup

class Scraper:
    def __init__(self):
        self.username = None
        self.password = None
        self.session = None
        self.dataDict = {'Brouillon': 'draft', "Création du l'ordre du payement": 'order_created', 'Validé(Ni signé ni payé)': 'validated_but_neither_signed_or_paid', "Confirmé par l'agent": 'confirmed_by_agent', 'Confirmé par le client': 'confirmed_by_web', 'Abandonné par le client': 'abandoned_by_web', "Abandonné par l'agent": 'abandoned_by_agent', 'Signé': 'signed', 'Parcours finalisé': 'finalized', 'Échéancier crée': 'payment_schedule_created', 'En attente de premier prélèvement': 'waiting_for_first_drawel', 'Iban frauduleux': 'fraudulous_iban', 'En attente du PDL valide': 'waiting_for_valid_pdl', 'En attente du PCE valide': 'waiting_for_valid_pce', 'En attente du PCE valide suite à un mismatch': 'mismatch_waiting_for_valid_pce', 'En attente du PDL valide suite à un mismatch': 'mismatch_waiting_for_valid_pdl', 'Offre non valide à cette date (non plus commercialisée)': 'non_valid_product_on_current_date', "Problème de detection de l'offre choisis": 'invalid_quotation_no_chosen_offer', 'Segment invalide du point de livraison': 'invalid_delivery_point_segment', 'Estimation invalide': 'invalid_quotation_negative_monthly_payment', "Date de début du contrat dépasse la date de validité de l'offre": 'invalid_start_date_against_offer_due_date', 'En attente de la validation de la vente': 'waiting_for_sale_validation', 'Vente validée par le contrôleur': 'sale_is_validated', "Vente n'est pas validée par le contrôleur": 'sale_is_not_validated', 'Contrat mis en attente': 'abandoned_with_stand_by', 'Contrat abandonner pour déménagement': 'abandoned_for_moving', "Contrat en attente d'abandon du contrat remplacé": 'waiting_for_abandoning_the_replaced_contract', 'en attente de paiement': 'waiting-prepay', 'En attente de paiement CTR GAZ': 'waiting-prepay-gas', 'En attente de paiement CTR GAZ, destiné pour les ventes à domicile': 'waiting-prepay-gas-vad', 'En attente des index pour effectuer le pre-paiement': 'waiting-prepay-no-sw', 'En attente des index pour effectuer le pre-paiement, aussi attente de délais légal pour les vente à domicile': 'waiting-prepay-no-sw-vad', 'Switch ASAP': 'prepay-no-sw', 'Attente fin délai rétractation': 'waiting-14d', 'Terminé NextEarth': 'terminatedNextEarth', 'Demande hors HGZ': 'sendToMktByPortal', 'Inactif (récupération)': 'Recovery', 'PP1 fait (à transférer à Odoo)': 'PP1doneToTransferOdoo', 'Abandonné (à transférer à Odoo)': 'abandonedToTransferOdoo', 'A valider': 'toValidate', 'Initialisé': 'initialized', 'En attente d`intervention (manuel)': 'waiting', 'Inactif (annulé par le marché)': 'Cancelled', 'Abandon manuel': 'abandoned', 'Abandon des contrats doublons': 'abandoned-duplicate', 'Inactif (rejet validation interne)': 'ValidationReject', 'Inactif (rejeté par le marché)': 'Rejected', 'PP1 rejeté par la banque': 'prepayRejected', 'Envoyé au marché': 'sendToMkt', 'Accepté': 'Accepted', 'Effectif': 'effective', 'Contrat qui a été actif, et qui est maintenant sorti du périmètre de livraison': 'terminated', 'Inconnue': 'unknown', 'En attente de paiement, destiné pour les ventes à domicile': 'waiting-prepay-vad', 'En attente de vérification - CHF/MES': 'waiting-verification-chf-mes', 'En attente de vérification - erreur PDL': 'waiting-verification-err-pdl', 'En attente de vérification - nom introuvable': 'waiting-verification-nom-introuvable'}

    def GetDataDict(self):
        return self.dataDict

    def CheckLogin(self, user, psw):
        url = "https://souscription.ohm-energie.com/login"
        self.session = requests.session()
        fg = self.session.get(url)
        soup = BeautifulSoup(fg.text, "html.parser")
        csrf = soup.find("input", {"name": "_csrf_token"})["value"]
        data = {
            "_csrf_token": csrf,
            "_username": user,
            "_password": psw,
            "source": "phone",
            "_submit": ""}
        fp = self.session.post(url, data=data)
        checkUrl = "https://souscription.ohm-energie.com/admin?crudAction=index&crudControllerFqcn=App%5CController%5CEasyAdmin%5CContractDraftColdController&entityFqcn=App%5CEntity%5CContractualDataCold&menuIndex=0&signature=B0HmGs4oP-Zw7DGkqJbf_W5ueiTbar1Kw1ActOgc-ec&submenuIndex=0"
        sp = self.session.get(checkUrl)
        if "login" in sp.url:
            return False
        else:
            self.username = user
            self.password = psw
            return True

    def GetSession(self):
        return self.session

    def Scrape(self, date, item):
        url = "https://souscription.ohm-energie.com/admin"
        admin = self.session.get(url)
        soup = BeautifulSoup(admin.text, "html.parser")
        baseLink = soup.find("ul", {"class": "submenu"}).find("a")["href"]
        signature = baseLink.split("signature=")[-1].split("&")[0]
        baseLink = baseLink.replace("https://souscription.ohm-energie.com","")
        if date:
            date = date+"T00:00"
            reqUrl = "https://souscription.ohm-energie.com/admin?referrer=%s&crudAction=index&crudControllerFqcn=App\Controller\EasyAdmin\ContractDraftColdController&entityFqcn=App\Entity\ContractualDataCold&menuIndex=0&signature=%s&submenuIndex=0&filters[createdAt][comparison]==&filters[createdAt][value]=%s&filters[createdAt][value2]=&filters[contractStatus][comparison]==&filters[contractStatus][value]=%s&page=1"%(baseLink, signature, date, item)
        else:
            reqUrl = "https://souscription.ohm-energie.com/admin?referrer=%s&crudAction=index&crudControllerFqcn=App\Controller\EasyAdmin\ContractDraftColdController&entityFqcn=App\Entity\ContractualDataCold&menuIndex=0&signature=%s&submenuIndex=0&filters[contractStatus][comparison]==&filters[contractStatus][value]=%s&page=1"%(baseLink, signature, item)

        builtReq = self.session.get(reqUrl)
        if "Aucun résultat trouvé" in builtReq.text:
            print("oops")
        else:
            soup = BeautifulSoup(builtReq.text, "html.parser")
            count = int(soup.find("div", {"class": "list-pagination-counter"}).find("strong").text.strip())
            if count % 20 == 0:
                count = count // 20
            else:
                count = (count // 20) + 1