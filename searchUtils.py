import pandas as pd
import re
import os.path
import time
import requests
import pyperclip
from bs4 import BeautifulSoup
from errorLogger import setup_logger


class searchUtils:
    def __init__(self):
        self.logger = setup_logger("searchUtilsLogger", "searchUtils_error_log.txt")
        self.pattern_subject = re.compile(
            r"\b(código|passcode|code|clave de un solo uso)\b"
        )
        self.pattern_subject_amazon_es = re.compile(
            r"amazon.com:.+[Ii]nicio\sde\ssesión"
        )
        self.pattern_subject_amazon_en = re.compile(r"amazon.com:\s[Ss]ign-in")
        self.pattern_password = re.compile(r"\b(contraseña|password)\b")
        self.pattern_netflix_access = re.compile(
            r"(netflix:\snueva\ssolicitud\sde\sinicio\sde\ssesión|netflix:\snew\ssign\-?\s?in\srequest|netflix:\snew\slog\s?in\srequest)"
        )
        self.pattern_netflix_suspended = re.compile(
            r"\b(netflix está suspendida|netflix is suspended)\b"
        )
        self.pattern_netflix_payment = re.compile(
            r"\b(importante: te queda un día para actualizar la forma de pago|one day left to update the payment method)\b"
        )
        self.pattern_transmiter = r"From:\s\"?(\w+)\"?"
        self.pattern_password_link = r"\[([^\]]+)\]"
        self.pattern_netflix_profile = r"\,\s?([a-zA-Z0-9À-ÿ]+\s?[a-zA-Z0-9À-ÿ]+)\s?\:"
        self.pattern_amazon_code_en = r"verification\scode\sis\:\s?(\d{6})"
        self.pattern_amazon_code_es = r"verificaci[óo]n\ses\:\s?(\d{6})"
        self.pattern_stardis_code_es = r"15\sminutos.\s(\d{6})"
        self.pattern_stardis_code_en = r"15\sminutes.\s(\d{6})"
        self.pattern_access_link_netflix = (
            r"\[(https\:\/\/www\.netflix\.com\/ilum\?code=.{8})\]"
        )
        self.pattern_payment_link_netflix = (
            r"\[(https\:\/\/www\.netflix\.com\/YourAccountPayment.*?)\]"
        )
        self.pattern_subject_code_temporal = (
            r"\[(https\:\/\/www\.netflix\.com\/account\/travel\/verify\?nftoken.*?)\]"
        )
        self.pattern_subject_code_operator = r"\b\d{4}\b"

    def identifyGmail(self, email: str):
        """
        metodo que verifica si es un correo
        parametro "email" <type: str>
        retorna True si es correo
        retorna False si no
        """
        # Expresión regular para validar correos de Gmail
        patron_gmail = r"^[a-zA-Z0-9._%+-]+@gmail\.com$"
        if re.match(patron_gmail, email.strip()):
            return True
        else:
            return False

    def cleanEmail(self, mail: str):
        """
        metodo que se encarga de limpiar el mail
        parametro "mail" <type: str>
        retorna el correo sin extensiones y sin espacios en blanco
        """
        patron = r"^(.*?)\+.+?(?=@.*$)"
        correo_limpio = re.sub(patron, r"\1", mail)
        return correo_limpio.strip()

    def passwordLinkIdentifier(self, body: str):
        """
        metodo que identifica el link de reinicio de contrasena de netflix
        parametro "body" <type: str>
        retorna el link
        """
        match = re.search(self.pattern_password_link, body)
        return match.group(1)

    def accessLinkIdentifier(self, body: str):
        """
        metodo que identifica el link de acceso sin contrasena de netflix
        parametro "body" <type:str>
        retorna el link
        """
        match = re.search(self.pattern_access_link_netflix, body)
        return match.group(1)

    def paymentLinkIdentifier(self, body: str):
        """
        metodo que identifica el link de pago de una cuenta de netflix que esta por vencerse
        parametro "body" <type:str>
        retorna el link
        """
        match = re.search(self.pattern_payment_link_netflix, body)
        return match.group(1)

    def serviceIdentifier(self, transmiter: str):
        """
        metodo se encarga de obtener el nombre de la plataforma del emisor del mensaje
        usando expresiones regulares
        parametro "transmiter" <type: str>
        retorna el servicio <type: str>
        """
        match = re.search(self.pattern_transmiter, transmiter)
        return match.group(1)

    def getTokenFolder(self, filename: str):
        """
        metodo que se encarga de obtener la carpeta de tokens objetiva
        parametro "filename" <type: str>
        retorna el nombre de la carpeta y si no retorna false
        """
        elements = os.listdir()
        for i in elements:
            if "tokens" not in i:
                continue
            else:
                if filename in os.listdir(os.path.join(i)):
                    return i + "/"
                else:
                    continue
        return None

    def getCredentials(self, mail: str):
        """
        metodo que se encarga de obtener las credenciales del dataframe
        parametro "mail" <type: str> es el correo al cual buscaremos en el excel
        el return credentials[0] es el correo
        el credentials[1] es la clave
        retorna una lista con los valores de credenciales
        """
        credentials = []
        excel_name = [i for i in os.listdir() if ".xlsx" in i][0]  # obtenemos el excel
        df = pd.read_excel(excel_name, sheet_name="CORREOS")
        # obtenemos la fila especifica
        email = self.cleanEmail(mail.lower())  # limpiamos el email

        df_lower = df.map(lambda x: x.lower() if isinstance(x, str) else x)
        # aqui obtenemos el dataframe con los datos especificos
        data = df[df_lower.isin([email.lower()]).any(axis=1)]
        # luego obtenemos el index location de cada uno de los datos especificados en la variable "data"
        # para asi ponerlos en una lista y luego iterar en ella
        try:
            credentials_dirty = [
                data.iloc[0, data.columns.get_loc(i)] for i in data.columns
            ]
        except Exception as e:
            return f"No encontre el acceso a ese correo, Por favor buscarlo en tabla, correo: \n{email}\n"

        for i, v in enumerate(credentials_dirty):
            if str(v) == "nan":
                pass
            elif email in str(v):
                credentials.append(str(v))
                credentials.append(credentials_dirty[i + 1])
        return credentials

    def getNetflixPageCode(self, url: str):
        """
        metodo que se encarga de ingresar a la URL del enlace de netflix para poder scrapear el codigo de 4 digitos
        parametro "url" es <type:str>
        retorna el codigo <type: int>
        """
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            # Busca en todo el texto de la página
            page_text = soup.get_text()
            # Usa una expresión regular para encontrar un código de 4 dígitos
            match = re.search(r"\.(\d{4})\w", page_text)
            if match:
                code = match.group(1)
                return "Código de 4 dígitos encontrado: " + code
            else:
                return "El codigo ya fue reclamado!"
        else:
            return (
                "Error al acceder al enlace. Código de estado: " + response.status_code
            )

    def getAmazonCode(self, body: str, target_service: str):
        """
        metodo que retorna el codigo de amazon
        parametro "body" <type:str>
        parametro "target_service" <type:str>
        retorna el string del codigo <type:str>
        """
        try:
            match_es = re.search(self.pattern_amazon_code_es, body)
            match_en = re.search(self.pattern_amazon_code_en, body)
            if match_es:
                return f"Su codigo de {target_service} es: {match_es.group(1)}\n"
            elif match_en:
                return f"Su codigo de {target_service} es: {match_en.group(1)}\n"
            else:
                error_message = f"Ha ocurrido un error en el método searchUtils.getAmazonCode, no hizo match. Body: \n{body}\n"
                self.logger.error(error_message)
                return (
                    "El mensaje no contenia un codigo, por favor verifica el correo\n"
                )
        except:
            error_message = f"Ha ocurrido un error en el método searchUtils.getAmazonCode, no hizo match. Body: \n{body}\n"
            self.logger.error(error_message)
            return "Se ha registrado un error, contacta con el programador para que lo solucione\n"

    def getDisStarCode(self, body: str, target_service: str):
        """
        metodo que retorna el codigo si es disney o star
        parametro "body" <type:str>
        parametro "target_service" <type:str>
        retorna el string del codigo <type:str>
        """
        try:
            match_es = re.search(self.pattern_stardis_code_es, body)
            match_en = re.search(self.pattern_stardis_code_en, body)
            if match_es:
                return f"Su codigo de {target_service} es: {match_es.group(1)}\n"
            elif match_en:
                return f"Su codigo de {target_service} es: {match_en.group(1)}\n"
            else:
                error_message = f"Ha ocurrido un error en el método searchUtils.getDisstarCode, no hizo match. Body: \n{body}\n"
                self.logger.error(error_message)
                return "Se ha registrado un error, contacta con el programador para que lo solucione\n"
        except:
            error_message = f"Ha ocurrido un error en el método searchUtils.getDisstarCode, no hizo match. Body: \n{body}\n"
            self.logger.error(error_message)
            return "Se ha registrado un error, contacta con el programador para que lo solucione\n"

    def getNetflixProfile(self, body: str):
        """
        metodo que utiliza una expresion regular para obtener el perfil quien esta haciendo el cambio
        parametro "body" es <type: str>
        retorna el nombre del perfil si lo encuentra <type: str>
        """
        try:
            match = re.search(self.pattern_netflix_profile, body)
            if match:
                profile = match.group(1)
                return "El perfil al cual fue enviado es este: " + profile + "\n"
            else:
                error_message = f"Ha ocurrido un error en el método searchUtils.getNetflixProfile, no hizo match. Body: \n{body}\n"
                self.logger.error(error_message)
                return "No encontre el perfil :(\n"
        except Exception as e:
            error_message = f"Ha ocurrido un error en el método searchUtils.getNetflixProfile, no hizo match. Body: \n{body}\n"
            self.logger.error(error_message)
            return "No encontre el perfil :(\n"

    def getPasswordReset(self, subject: str):
        """
        metodo que se usa para identificar si se pidio un cambio de contrasena de netflix
        parametro "subject" es <type: str>
        retorna True si es un contrasena
        retorna False si no
        """
        if self.pattern_password.search(subject.lower()):
            return True
        else:
            return False

    def getNetflixAccessRequest(self, subject: str):
        """
        metodo que se encarga de identificar el asunto de una autorizacion de inicio de sesion en netflix
        parametro "subject" es <type: str>
        retorna True si es una autorizacion
        retorna False si no
        """
        if self.pattern_netflix_access.search(subject.lower()):
            return True
        else:
            return False

    def getNetflixPayment(self, subject: str):
        """
        metodo que se encarga de identificar el asunto de una cuenta que esta por pagarse
        parametro "subject" es <type: str>
        retorna True si es una autorizacion
        retorna False si no
        """
        if self.pattern_netflix_payment.search(subject.lower()):
            return True
        else:
            return False

    def getNetflixSuspended(self, subject: str):
        """
        metodo que se encarga de identificar el asunto de una cuenta suspendida de netflix
        parametro "subject" es <type: str>
        retorna True si es una autorizacion
        retorna False si no
        """
        if self.pattern_netflix_suspended.search(subject.lower()):
            return True
        else:
            return False

    def getSubjectMessage(self, subject: str):
        """
        metodo que se utiliza para saber si el asunto del mensaje es codigo o no
        parametro "subject" es <type: str>
        retorna True si es un codigo
        retorna False si no es un codigo
        """
        if self.pattern_subject.search(subject.lower()):
            return True
        else:
            return False

    def getAmazonSubjectMessage(self, subject: str):
        """
        metodo que se usa para saber si es un correo amazon o no
        parametro "subject" <type: str>
        retorna True si es un codigo amazon
        retorna False si no
        """
        if self.pattern_subject_amazon_es.search(subject.lower()):
            return True
        elif self.pattern_subject_amazon_en.search(subject.lower()):
            return True
        else:
            return False

    def getSubjectMatter(self, body: str):
        """
        metodo que se encarga de identificar el asunto del mensaje y lo clasifica en codigo temporal o de operador para netflix
        parametro "body" <type: str>
        retorna siempre el "match" <type: str>
        retorna un 0 si es un codigo temporal
        retorna un 1 si es un codigo operador
        da error si no es ninguno de los dos
        """
        try:
            match_temporal = re.search(self.pattern_subject_code_temporal, body)
            match_operator = re.search(self.pattern_subject_code_operator, body)
            if match_temporal:  # aqui es cuando es un codigo de acceso temporal
                return [match_temporal.group(1), 0]
            elif match_operator:  # aqui es cuando es un codigo de acceso para operador
                return [match_operator.group(), 1]
            else:  # aqui es cuando no es ninguno de los dos y dio error
                error_message = f"Ha ocurrido un error en el método searchUtils.getSubjectMatter, no hizo match. Body: \n{body}\n"
                self.logger.error(error_message)
                return "Se ha registrado un error, contacta con el programador para que lo solucione\n"
        except Exception as e:
            error_message = f"Ha ocurrido un error en el método searchUtils.getSubjectMatter, no hizo match. Body: \n{body}\n"
            self.logger.error(error_message)
            return "Se ha registrado un error, contacta con el programador para que lo solucione\n"

    def copyInPaperclip(self, credentials: list):
        """
        metodo que copia las credenciales en el portapeles
        parametro "credentials" <type: list>
        no retorna nada
        """
        for i in credentials[::-1]:  ##se hace asi para pode invertir la lista
            time.sleep(0.5)
            pyperclip.copy(i)
