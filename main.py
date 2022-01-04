import json
from icalendar import Calendar, Event
from datetime import datetime
import os
from plyer import notification
from threading import Thread
import pytz
import time
utc = pytz.UTC


class Logger:
    f = open('log.txt', 'a')

    def WriteMessage(self, message):
        now = datetime.now()
        self.f.write(str(now) + '\n')
        self.f.write(message)
        self.f.flush()


logger = Logger()


class Alert(Thread):
    title = ''
    message = ''
    timeout = ''
    repetitions = 0

    def __init__(self, title, message, timeout, repetitions):
        super().__init__()
        self.title = title
        self.message = message
        self.timeout = timeout
        self.repetitions = repetitions

    def run(self):
        for index in range(0, self.repetitions):
            notification.notify(
                title=self.title + str(index),
                message=self.message,
                timeout=self.timeout
            )
            time.sleep(30)


class ManageAlerts(Thread):
    alerts = []

    def add_alert(self, alert, trigger_time):
        self.alerts.append([alert, trigger_time])
        logger.WriteMessage("Added alert to alert list!\n")

    def run(self):
        logger.WriteMessage(".....Alert manager is now running......\n")
        while True:
            now = datetime.now().replace(tzinfo=utc)
            for alert in self.alerts:
                if alert[1] < now:
                    alert[0].start()
                    self.alerts.remove(alert)


manager = ManageAlerts()
manager.start()


def IterateThroughFiles():
    logger.WriteMessage("Iterating through files!")
    for file in os.listdir():
        if file.endswith(".ics"):
            logger.WriteMessage("Found .ics files\n")
            ParseIcs(ReadEventFromFileIcs(file))
        if file.endswith(".json"):
            logger.WriteMessage("Found .json files\n")
            ParseJson(ReadEventFromFileJson(file))


def ReadEventFromFileJson(path):
    f = open(path, 'r')
    dictionary = json.load(f)
    return dictionary


def ParseJson(dictionary):
    start_date = ''  # actual date of the event
    end_date = ''  # end date of event
    trigger = datetime.now()
    repetitions = 1
    duration = 0
    action = ''
    attendee = ''  # if action is type email
    description = ''
    summary = ''
    attach_type = ''
    if dictionary['start_date'] is not None:
        start_date = dictionary['start_date']
    if dictionary['end_date'] is not None:
        end_date = dictionary['end_date']
    for alert in dictionary['alert']:
        if alert['trigger'] is not None:
            trigger = alert['trigger']
        if alert['action'] is not None:
            action = alert['action']
        if alert['summary'] is not None:
            summary = alert['summary']
        if alert['description'] is not None:
            description = alert['description']
        if alert['attach_type'] is not None:
            attach_type = alert['attach_type']
        if alert['attendee'] is not None:
            attendee = alert['attendee']
        if alert['repetitions'] is not None:
            repetitions = alert['repetitions']
        start_date = datetime.strptime(start_date, '%b %d %Y %I:%M%p')
        trigger = datetime.strptime(trigger, '%b %d %Y %I:%M%p')
        end_date = datetime.strptime(end_date, '%b %d %Y %I:%M%p')
        trigger = trigger.replace(tzinfo=utc)
        CreateAlert(start_date, end_date, trigger, repetitions, duration, action, attendee, description, summary, attach_type)


def ReadEventFromFileIcs(path):
    f = open(path, 'r')
    all_text = f.read()
    f.close()
    return all_text


def ParseIcs(plain_text):
    cal = Calendar.from_ical(plain_text)
    event_date = ''  # actual date of the event
    event_end = ''  # end date of event
    trigger_time = datetime.now()
    repetitions = 1
    duration = 0
    action = ''
    attendee = ''  # if action is type email
    description = ''
    summary = ''
    attach_type = ''
    for component in cal.walk():
        if component.name == "VEVENT":
            event_date = component.get('dtstart').dt
            event_end = component.get('dtend').dt
        if component.name == "VALARM":
            summary = component.get('summary')
            description = component.get('description')
            attach_type = component.get('attach')
            action = component.get('action')
            if component.get('duration') is not None:
                duration = component.get('duration').dt
            repetitions = component.get('repeat')
            if component.get('trigger') is not None:
                trigger_time = component.get('trigger').dt
            attendee = component.get('attendee')
    trigger_time = event_date + trigger_time
    trigger_time = trigger_time.replace(tzinfo=utc)
    if repetitions is None:
        repetitions = 1
    print(trigger_time)
    CreateAlert(event_date, event_end, trigger_time, repetitions, duration, action, attendee, description, summary,
                attach_type)


def CreateAlert(event_date, event_end, trigger_time, repetitions, duration, action, attendee, description, summary,
                attach_type):
    alert = Alert("Alert! " + summary,
                  "Type: " + action + "\n" + description,
                  15,
                  repetitions)
    logger.WriteMessage("Created an alert!\n")
    manager.add_alert(alert, trigger_time)


if __name__ == '__main__':
    logger.WriteMessage("----------------\nStarted tool\n----------------\n")
    IterateThroughFiles()
    logger.WriteMessage("-----------------")
