import base64
import pytz
import pickle
import os.path
import json
from errorLogger import setup_logger
from searchUtils import searchUtils
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
from requests.exceptions import ConnectionError, Timeout, RequestException
from googleapiclient.errors import HttpError

search_utils = searchUtils()


class authGoogle:
    def __init__(self):
        self.logger = setup_logger("authGoogleLogger", "authGoogle_error_log.txt")

    def runEmails(self, target_email: str):
        """
        metodo principal que se encarga de correr todo el programa
        muestra los correos electrónicos enviados hace 15 minutos.
        parametro "target_email" <type: str>
        retornamos el mensaje
        """
        mails = []
        credential = search_utils.cleanEmail(target_email)
        try:
            now = datetime.now(pytz.utc)
            past_15 = now - timedelta(minutes=15)
            query = f"after:{int(past_15.timestamp())} to:{target_email.strip()}"
            # obtenemos el correo padre (sin extensiones)
            service = self.getService(credential)
            if type(service) == str:  # no hay tokens creadas para este correo
                return service
            else:
                results = (
                    service.users()
                    .messages()
                    .list(userId="me", labelIds=["INBOX"], q=query)
                    .execute()
                )
                messages = results.get("messages", [])
                if not messages:
                    return f"No hay correos en los ultimos 15 minutos para la cuenta: {target_email}\npor favor decirle al cliente que no ha llegado\n"
                else:
                    for message in messages[
                        :10
                    ]:  # Lee los primeros 15 correos no leídos
                        msg = self.getMessage(service, "me", message["id"])
                        if not msg:
                            continue
                        else:
                            mails.append(msg + "\n")
                    return "".join(mails[::-1])

        except RefreshError:
            error_message = f"Ha ocurrido un error en el método authGoogle.runEmails, las credenciales se vencieron; Correo: \n{target_email}\n"
            self.logger.error(error_message)
            return (
                f"La credencial ya esta vencida, el programador la renovara en breves\n"
            )
        except ConnectionError:
            error_message = f"Ha ocurrido un error en el método authGoogle.runEmails, conexion a internet\n "
            self.logger.error(error_message)
            return "Error de conexión. Verifica tu conexión a Internet y vuelve a intentarlo\n"
        except Timeout:
            error_message = f"Ha ocurrido un error en el método authGoogle.runEmails, timeout error "
            self.logger.error(error_message)
            return "La solicitud ha superado el tiempo de espera. Inténtalo de nuevo más tarde\n"
        except RequestException as e:
            error_message = f"Ha ocurrido un error en el método authGoogle.runEmails, error en la solicitud \n{e}\n"
            self.logger.error(error_message)
            return f"Se ha producido un error en la solicitud, vuelve a intentarlo en 1 minuto\n"
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                error_message = f"Ha ocurrido un error en el metodo authGoogle.runEmails, error \n{e}\n"
                self.logger.error(error_message)
                return f"Ha ocurrido un error de parte de Google, por favor vuelve a intentarlo dentro de 1 minuto\n"
            else:
                error_message = f"Ha ocurrido un error en el metodo authGoogle.runEmails, error \n{e}\n"
                self.logger.error(error_message)
                return f"Ha ocurrido un error de conexion, por favor notificale al progamador\n"
        except Exception as error:
            error_message = f"Ha ocurrido un error en el método authGoogle.runEmails \n{error}\n{target_email}\n"
            self.logger.error(error_message)
            return f"Ha ocurrido un error en el programa, por favor avisar al programador\n"

    def lookAmazonBlocked(self, target_email: str):
        """
        metodo que se encarga de verificar si la cuenta de amazon esta bloqueada
        parametro "target_email" <type: str>
        retornamos el mensaje
        """
        credential = search_utils.cleanEmail(target_email)
        try:
            subject_query = "Your Amazon account has been suspended"
            query = f"to:{target_email.strip()} subject:{subject_query}"
            # obtenemos el correo padre (sin extensiones)
            service = self.getService(credential)
            if type(service) == str:  # no hay tokens creadas para este correo
                return service
            else:
                results = (
                    service.users()
                    .messages()
                    .list(userId="me", labelIds=["INBOX"], q=query)
                    .execute()
                )
                messages = results.get("messages", [])
                if not messages:  # activa
                    return f"La cuenta de amazon esta ACTIVA!\n"
                else:
                    for message in messages[:5]:  # bloqueada
                        return "La cuenta de amazon esta BLOQUEADA :(\n"

        except RefreshError:
            error_message = f"Ha ocurrido un error en el método authGoogle.lookAmazonBlocked, las credenciales se vencieron; Correo: \n{target_email}\n"
            self.logger.error(error_message)
            return (
                f"La credencial ya esta vencida, el programador la renovara en breves\n"
            )
        except ConnectionError:
            error_message = f"Ha ocurrido un error en el método authGoogle.lookAmazonBlocked, conexion a internet\n "
            self.logger.error(error_message)
            return "Error de conexión. Verifica tu conexión a Internet y vuelve a intentarlo\n"
        except Timeout:
            error_message = f"Ha ocurrido un error en el método authGoogle.lookAmazonBlocked, timeout error "
            self.logger.error(error_message)
            return "La solicitud ha superado el tiempo de espera. Inténtalo de nuevo más tarde\n"
        except RequestException as e:
            error_message = f"Ha ocurrido un error en el método authGoogle.lookAmazonBlocked, error en la solicitud \n{e}\n"
            self.logger.error(error_message)
            return f"Se ha producido un error en la solicitud, vuelve a intentarlo en 1 minuto\n"
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                error_message = f"Ha ocurrido un error en el metodo authGoogle.lookAmazonBlocked, error \n{e}\n"
                self.logger.error(error_message)
                return f"Ha ocurrido un error de parte de Google, por favor vuelve a intentarlo dentro de 1 minuto\n"
            else:
                error_message = f"Ha ocurrido un error en el metodo authGoogle.lookAmazonBlocked, error \n{e}\n"
                self.logger.error(error_message)
                return f"Ha ocurrido un error de conexion, por favor notificale al progamador\n"
        except Exception as error:
            error_message = f"Ha ocurrido un error en el método authGoogle.lookAmazonBlocked \n{error}\n{target_email}\n"
            self.logger.error(error_message)
            return f"Ha ocurrido un error en el programa, por favor avisar al programador\n"

    def lookNetflixSuspended(self, target_email: str):
        """
        metodo que se encarga de verificar si la cuenta de amazon esta bloqueada
        parametro "target_email" <type: str>
        retornamos el mensaje
        """
        credential = search_utils.cleanEmail(target_email)
        try:
            mails = []
            subject_query = "Netflix está suspendida"
            subject_query_2 = "Netflix has been suspended"
            subject_query_3 = "Actualizar la forma de pago"
            query = f'to:{target_email.strip()} subject:"{subject_query}" OR subject:"{subject_query_2}" OR subject:"{subject_query_3}"'
            # obtenemos el correo padre (sin extensiones)
            service = self.getService(credential)
            if type(service) == str:  # no hay tokens creadas para este correo
                return service
            else:
                results = (
                    service.users()
                    .messages()
                    .list(userId="me", labelIds=["INBOX"], q=query)
                    .execute()
                )
                messages = results.get("messages", [])
                if not messages:
                    return f"No detecte mensajes de cuentas suspendidas\n"
                else:
                    for message in messages[:5]:
                        msg = self.getMessage(service, "me", message["id"])
                        if not msg:
                            continue
                        else:
                            mails.append(msg + "\n")
                    return "".join(mails[::-1])

        except RefreshError:
            error_message = f"Ha ocurrido un error en el método authGoogle.lookNetflixSuspended, las credenciales se vencieron; Correo: \n{target_email}\n"
            self.logger.error(error_message)
            return (
                f"La credencial ya esta vencida, el programador la renovara en breves\n"
            )
        except ConnectionError:
            error_message = f"Ha ocurrido un error en el método authGoogle.lookNetflixSuspended, conexion a internet\n "
            self.logger.error(error_message)
            return "Error de conexión. Verifica tu conexión a Internet y vuelve a intentarlo\n"
        except Timeout:
            error_message = f"Ha ocurrido un error en el método authGoogle.lookNetflixSuspended, timeout error "
            self.logger.error(error_message)
            return "La solicitud ha superado el tiempo de espera. Inténtalo de nuevo más tarde\n"
        except RequestException as e:
            error_message = f"Ha ocurrido un error en el método authGoogle.lookNetflixSuspended, error en la solicitud \n{e}\n"
            self.logger.error(error_message)
            return f"Se ha producido un error en la solicitud, vuelve a intentarlo en 1 minuto\n"
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                error_message = f"Ha ocurrido un error en el metodo authGoogle.lookNetflixSuspended, error \n{e}\n"
                self.logger.error(error_message)
                return f"Ha ocurrido un error de parte de Google, por favor vuelve a intentarlo dentro de 1 minuto\n"
            else:
                error_message = f"Ha ocurrido un error en el metodo authGoogle.lookNetflixSuspended, error \n{e}\n"
                self.logger.error(error_message)
                return f"Ha ocurrido un error de conexion, por favor notificale al progamador\n"
        except Exception as error:
            error_message = f"Ha ocurrido un error en el método authGoogle.lookNetflixSuspended \n{error}\n{target_email}\n"
            self.logger.error(error_message)
            return f"Ha ocurrido un error en el programa, por favor avisar al programador\n"

    def getService(self, account: str):
        """
        metodo que se encarga de obtener la autenticacion de gmail
        si es exitosa obtenemos el servicio
        parametro account <type: str>
        retorna el servicio con la API ya lista
        """
        creds = self.authenticate(account)
        if type(creds) == str:
            return creds  # caso de que la crendencial no haya sido registrada aun
        else:
            service = build("gmail", "v1", credentials=creds)
            return service

    def getMessage(self, service, user_id, msg_id):
        """
        metodo que se encarga de obtener el mensaje para luego poder procesarlo
        parametro "service" hace referencia a la cuenta que estamos ingresando
        parametro "user_id" hace referencia al id que estamos ingresando
        parametro "msg_id" hace referencia al id del mensaje que estamos obteniendo
        retorna el msg_str se trabaja <type:str>
        """
        try:
            message = (
                service.users()
                .messages()
                .get(userId=user_id, id=msg_id, format="full")
                .execute()
            )
            msg_str = ""
            payload = message["payload"]
            headers = payload["headers"]

            asunto = ""
            para = ""  # cuenta receptora del correo
            sender = ""  # quien lo envia

            for header in headers:
                if header["name"] == "Subject":
                    msg_str += f"Asunto: {header['value']}\n"
                    asunto = f"Subject: {header['value']}"
                if header["name"] == "From":
                    sender = f"From: {header['value']}\n"
                if header["name"] == "To":
                    para += header["value"]
                    msg_str += f"Para: {header['value']}\n"

            # Convertir a segundos
            internal_date = int(message["internalDate"]) / 1000.0
            date_received = datetime.fromtimestamp(
                internal_date, tz=pytz.timezone("Etc/GMT+4")
            )
            msg_str += f"Hora de llegada: {date_received.strftime('%I:%M %p')}\n"
            # aqui deberia de estar la parte en donde nosotros identificamos si es un codigo o no
            # aqui identificamos si es un codigo
            if search_utils.getSubjectMessage(asunto):
                return self.serviceHandler(payload, msg_str, sender)
            elif search_utils.getAmazonSubjectMessage(asunto):  # codigo de amazon
                return self.serviceHandler(payload, msg_str, sender)
            # aqui identificamos que no es un codigo
            else:
                if (
                    search_utils.getPasswordReset(asunto)
                    and "netflix" in sender.lower()
                ):
                    return f"este es el link de reestablecer contrasena de netflix: [Haz click aqui]({self.getNetflixPwdLink(payload)})\n"
                elif (
                    search_utils.getNetflixAccessRequest(asunto)
                    and "netflix" in sender.lower()
                ):
                    return f"este es el link de permitir acceso sin contrasena de netflix: [Haz click aqui]({self.getNetflixAccessLink(payload)})\n"
                elif (
                    search_utils.getNetflixSuspended(asunto)
                    or search_utils.getNetflixPayment(asunto)
                ) and "netflix" in sender.lower():
                    return f"{asunto}: ({para}): [Haz click aqui]({self.getNetflixPaymentLink(payload)})\nRecibido el: {datetime.fromisoformat(str(date_received)).strftime('%m/%d/%Y')} a la hora: {date_received.strftime('%I:%M %p')}\n"
                else:
                    return f"Han llegado mensajes al correo, pero no son codigos: {asunto}\n"

        except Exception as error:
            error_message = (
                f"Ha ocurrido un error en el método authGoogle.getMessage \n{error}\n"
            )
            self.logger.error(error_message)
            return None

    def getCompleteMsg(self, payload: dict):
        """
        metodo se encarga de subdividir el json del mensaje "payload" para tratarlo por partes
        parametro "payload" es un <type: dict>
        retornar el body <type: str>
        """
        parts = payload.get("parts", [])
        if parts:
            for part in parts:  # mayoritariamente correos de netflix
                if part["mimeType"] == "text/plain":
                    data = part["body"]["data"]
                    decoded_data = base64.urlsafe_b64decode(data).decode("utf-8")
                    body = f"Body:\n{' '.join(decoded_data.split())}\n"
                    return body
                elif part["mimeType"] == "text/html":  # mayoritariamente correos amazon
                    data = part["body"]["data"]
                    decoded_data = base64.urlsafe_b64decode(data).decode("utf-8")
                    soup = BeautifulSoup(decoded_data, "html.parser")
                    body = f"Body:\n{' '.join(soup.get_text().split())}\n"
                    return body
        elif not parts:  # mayoritariamente correos de disney y correos de star
            data = payload["body"]["data"]
            decoded_data = base64.urlsafe_b64decode(data).decode("utf-8")
            soup = BeautifulSoup(decoded_data, "html.parser")
            body = f"Body (HTML):\n{' '.join(soup.get_text().split())}\n"
            return body

    def getNetflixPwdLink(self, payload: dict):
        """
        metodo que obtiene el link de cambio de contrasena de netflix
        parametro "payload" <type: dict>
        retorna el link
        """
        body = self.getCompleteMsg(payload)
        return search_utils.passwordLinkIdentifier(body)

    def getNetflixAccessLink(self, payload: dict):
        """
        metodo que obtiene el link de acceso de una cuenta de netflix
        parametro "payload" <type: dict>
        retorna el link
        """
        body = self.getCompleteMsg(payload)
        return search_utils.accessLinkIdentifier(body)

    def getNetflixPaymentLink(self, payload: dict):
        """
        metodo que obtiene el link de acceso de pago de una cuenta que esta por vencerse de netflix
        parametro "payload" <type: dict>
        retorna el link
        """
        body = self.getCompleteMsg(payload)
        return search_utils.paymentLinkIdentifier(body)

    def serviceHandler(self, payload: dict, msg_str: str, sender: str):
        """
        este metodo se encarga de identificar con que plataforma estamos tratando
        dependiendo de la plataforma se toman diferentes medidas
        parametro "payload" <type: dict>
        parametro "msg_str" <type: str>
        parametro "sender" <type: str> sender hace referencia al asunto del mensaje
        siempre retorna el "msg_str"
        """
        body = self.getCompleteMsg(payload)
        service = search_utils.serviceIdentifier(sender).lower()
        platforms = ["netflix", "disney", "star", "amazon"]
        if service == platforms[0]:  # es netflix
            # identificamos si el asunto es codigo temporal o de operador
            identifier = search_utils.getSubjectMatter(body)
            if type(identifier) == type(str):  # caso de que de error
                return identifier
            else:
                if identifier[1] == 0:  # codigo temporal
                    # obtenemos el nombre del perfil
                    msg_str += search_utils.getNetflixProfile(body)
                    # obtenemos el codigo
                    msg_str += search_utils.getNetflixPageCode(identifier[0]) + "\n"
                    return msg_str
                else:  # codigo de operador
                    msg_str += (
                        "este es el codigo de inicio de sesion para los operadores: "
                        + identifier[0]
                        + "\n"
                    )
                    return msg_str
        elif service == platforms[1] or service == platforms[2]:  # es disney o star
            target_service = platforms[platforms.index(service)]
            msg_str += search_utils.getDisStarCode(body, target_service)
            return msg_str
        elif service == platforms[3]:  # es amazon
            target_service = platforms[platforms.index(service)]
            msg_str += search_utils.getAmazonCode(body, target_service)
            return msg_str

    def authenticate(self, account: str):
        """
        metodo para poder autenticarnos con las cuentas
        parametro "account" <type: str>
        este metodo siempre retorna unas credenciales
        si no encuentra credenciales nos manda a auntenticarnos
        luego de que nos autenticamos el metodo se encarga de almacenar las credenciales
        """
        creds = None
        token_file = f"token_{account}.pickle"
        token_folder = search_utils.getTokenFolder(token_file)
        # el token file nos guardara las credenciales de inicio de sesion
        # se crea automaticamente cuando se autentica el procedimiento
        if token_folder:  # si token folder existe y tiene al archivo adentro
            with open(token_folder + token_file, "rb") as token:
                creds = pickle.load(token)
        # Se verifican si no hay credenciales o si estan invalidas
        if not creds or not creds.valid:
            # credenciales invalidas o expiradas
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())  # esta linea reestablece las credenciales
                with open(token_folder + token_file, "wb") as token:
                    pickle.dump(creds, token)
                return creds
            else:  # no hay credenciales y le vamos a informar esto al operador
                token_error_file = "sin_acceso.json"

                # Leer el archivo JSON existente o crear uno nuevo
                if os.path.exists(token_error_file):
                    with open(token_error_file, "r") as f:
                        accounts = json.load(f)
                else:
                    accounts = []

                # Verificar si el account ya está en la lista
                if account not in accounts:
                    accounts.append(account)
                    with open(token_error_file, "w") as f:
                        json.dump(accounts, f, indent=4)

                    return f"El correo {account} no se ha registrado, el programador prontamente lo registrara\n"

                else:
                    return f"El correo {account} no se ha registrado, el programador prontamente lo registrara\n"

        return creds
