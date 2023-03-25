from bs4 import BeautifulSoup
import requests
import sys
import smtplib
from email.message import EmailMessage
import config

ALL_NATIONS = [
    "Stockholms nation",
    "Norrlands nation",
    "Värmlands nation",
    "Gästrike-Hälsinge nation",
    "Östgöta nation",
    "Västgöta nation",
    "Kalmar nation",
    "Uplands nation",
    "Göteborgs nation",
    "Västmanlands-Dala nation",
    "Södermanlands-Nerikes nation",
    "Gotlands nation",
    "Smålands nation"
]

URL = "https://nationsguiden.se/"

## email recipients, kept in dedicated file for privacy reasons
EMAIL_LIST = config.EMAIL_LIST

## bot credentials, kept in dedicated file for privacy reasons
BOT_EMAIL = config.BOT_EMAIL
BOT_PASSWORD = config.BOT_PASSWORD

## to turn the data from the website into objects that we can work with
class Event:
    def __init__(self, nation, event_name, start_time, end_time):
        self.nation = nation
        self.event_name = event_name
        self.start_time = start_time
        self.end_time = end_time

# events on the website are grouped by category
def get_events_from_category(event_category) -> list:
        events = soup.find(id=event_category)
        if events: event_names = events.find_all("li")
        else: return []

        out = []

        for i in event_names:
            nation = i.find(class_="a").get_text().strip()
            event_name = i.find(class_="event-item-title").get_text().strip()

            ## work around the fact that there are 2 <small> under each event
            smalls = i.find_all("small")
            time_string = smalls[-1].get_text()
            start_time = time_string[5:10]
            end_time = None
            if len(time_string) > 19:
                end_time = time_string[20:]
            else:
                end_time = time_string[14:19]
            
            out.append(Event(nation, event_name, start_time, end_time))
        
        return out

def count_distinct_nations(events) -> int:
    nations = [x.nation for x in events]
    nations = list(dict.fromkeys(nations))
    return len(nations)

# returns a list of the names of all nations 
# that DO NOT have events today
def get_unrepresented_nations(events) -> list:
    nations = [e.nation for e in events]
    out = []
    for a in ALL_NATIONS:
        if a not in nations:
            out.append(a)
    return out

def send_email(receiver, subject, message) -> bool:
    try:
        msg = EmailMessage()
        msg.set_content(message)
        msg['subject'] = subject
        msg['to'] = receiver
        msg['from'] = BOT_EMAIL

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(BOT_EMAIL, BOT_PASSWORD)
        server.send_message(msg)
        server.quit()

        return True
    except:
        return False

## send email with status report
def trigger_sendout(all_events):
    subject = f"Idag har {count_distinct_nations(all_events)} nationer öppet!"
    message = f"""Idag har {count_distinct_nations(all_events)} nationer öppet.\nDet innebär att en LPC (Lengendary Pub Crawl) är möjlig.\nNedan följer en lista på dagens evenemang:\n\n\n"""
    for e in all_events:
        event = f"{e.nation}\n{e.event_name}\nÖppnar: {e.start_time}\nStänger: {e.end_time}\n\n"
        message += event
    message += f"\n\nFör mer info, besök {URL}\nVad väntar du på? Börja planera!"

    for e in EMAIL_LIST:
        if send_email(e, subject, message):
            print(f"A mail regarding a LPC has been sent to {e}")
        else:
            print(f"There was an error when trying to send the email to {e}")


if __name__ == "__main__":
    print("\nLPCDetector 3.0 by Fredrik Gustafsson")

    ## events on the website are grouped by category
    ## we want to search for events that are classified as
    ## pub, club or restaurant
    categories = ["event-category-9", "event-category-10", "event-category-5"]

    print(f"Fetching data from {URL}...\n")
    page = requests.get(URL)
    if page.status_code != 200:
        sys.exit(f"{page.status_code} Error: Request for {URL} could not be handled.")

    soup = BeautifulSoup(page.text, "html.parser")

    ## fetch all events that are listed under either
    ## of the categories we are interested in
    all_events = []
    for i in categories:
        all_events.extend(get_events_from_category(i))

    ## determine whether or not a LPC is possible
    if count_distinct_nations(all_events) < len(ALL_NATIONS):
        ## a LPC is not possible
        print(f"There are {count_distinct_nations(all_events)} out of {len(ALL_NATIONS)} nations open today.")
        print("There is no possible LPC today.")

        unrepresented = get_unrepresented_nations(all_events)
        print("The following nations are not open: ")
        for i in unrepresented:
            print(f"\t- {i}")
    else:
        ## POSSIBLE LPC!
        print(f"There are {count_distinct_nations(all_events)} nations open today.")
        print("There is a possible LPC today!")
        trigger_sendout(all_events)