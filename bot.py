import discord
import asyncio
from datetime import datetime
from discord.ext import commands
from authGoogle import authGoogle
from searchUtils import searchUtils
from time import time
from collections import defaultdict


TOKEN = "tu token"

intents = discord.Intents.default()
intents.message_content = True  # Necesario para leer el contenido de los mensajes
client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix="!", intents=intents)
code_absorber = authGoogle()
search_utils = searchUtils()

user_requests = defaultdict(list)
email_operators = {}
user_blocked = {}

REQUEST_LIMIT = 4
TIME_PERIOD = 10
BLOCK_TIME = 4 * 60
WINDOW_TIME = 40


@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        user_id = message.author.id
        current_time = time()

        if user_id not in user_blocked:
            user_blocked[user_id] = 0

        # Verifica si el usuario está bloqueado
        if current_time < user_blocked[user_id]:
            remaining_block_time = int(user_blocked[user_id] - current_time)
            await message.author.send(
                f"No puedes enviar más solicitudes durante {remaining_block_time // 60} minutos y {remaining_block_time % 60} segundos."
            )
            return

        # Filtra las solicitudes antiguas
        user_requests[user_id] = [
            timestamp
            for timestamp in user_requests[user_id]
            if current_time - timestamp < TIME_PERIOD
        ]

        if len(user_requests[user_id]) >= REQUEST_LIMIT:
            user_blocked[user_id] = current_time + BLOCK_TIME
            await message.author.send(
                "Estás enviando muchos mensajes No podrás enviar más solicitudes durante 4 minutos."
            )
            return

        user_requests[user_id].append(current_time)
        await mainFunc(message)

    else:  # se escribio en otro canal
        return


async def handle_registration_timeout(user_email, author_id):
    await asyncio.sleep(WINDOW_TIME)
    if (
        user_email in email_operators
        and email_operators[user_email]["operator"] == author_id
    ):
        del email_operators[user_email]


async def mainFunc(message):

    if message.content.endswith(" -r"):
        user_email = message.content.split(" ")[0]
        if search_utils.identifyGmail(str(user_email)):
            current_time = datetime.now()
            # verificamos si el email esta siendo trabajado por otro operador
            if user_email in email_operators:
                current_operator = email_operators[user_email]["operator"]
                if current_operator != message.author.id:
                    await message.author.send(
                        f"El operador {email_operators[user_email]['name']} está cambiando la contraseña de este correo."
                    )
                    return
            # registramos los datos del operador
            email_operators[user_email] = {
                "operator": message.author.id,
                "name": message.author,
                "time": current_time,
            }
            await message.author.send(
                f"Has sido registrado para el cambio de contraseña, tienes 40 segundos"
            )
            emails = code_absorber.runEmails(str(user_email.lower()))
            emails += f"Para el operador: {message.author}"
            await message.author.send(emails)
            # Iniciar una tarea asíncrona para manejar el tiempo de espera
            asyncio.create_task(
                handle_registration_timeout(user_email, message.author.id)
            )
        else:
            await message.author.send(
                f"Eso no es un correo Gmail, por favor ingresa un correo válido"
            )
    elif message.content.endswith(" -c"):  # busca si el correo amazon esta bloqueado
        user_email = message.content.split(" ")[0]
        if search_utils.identifyGmail(str(user_email)):
            emails = code_absorber.lookAmazonBlocked(str(user_email.lower()))
            emails += f"Para el operador: {message.author}"
            await message.author.send(emails)
        else:
            await message.author.send(
                f"Eso no es un correo Gmail, por favor ingresa un correo válido"
            )
    elif message.content.endswith(
        " -n"
    ):  # busca los correos netflix suspendidos mas recientes
        user_email = message.content.split(" ")[0]
        if search_utils.identifyGmail(str(user_email)):
            emails = code_absorber.lookNetflixSuspended(str(user_email.lower()))
            emails += f"Para el operador: {message.author}"
            await message.author.send(emails)
        else:
            await message.author.send(
                f"Eso no es un correo Gmail, por favor ingresa un correo válido"
            )
    else:
        if search_utils.identifyGmail(str(message.content)):
            emails = code_absorber.runEmails(str(message.content.lower()))
            emails += f"Para el operador: {message.author}"
            await message.author.send(emails)
        else:
            await message.author.send(
                f"Eso no es un correo Gmail, por favor ingresa un correo válido"
            )


# Ejecutar el bot
bot.run(TOKEN)
