from pymsteams import connectorcard
from JMAWeb import JMAWebURLs

class MSTeams:
    def __init__(self, webhook_url, mention_uid, mention_display_name):
        self.teams = connectorcard(webhook_url)
        self.mention_uid = mention_uid
        self.mention_display_name = mention_display_name

    def __create_mention_payload(self, obs, city, warning, status, dt):
        mention_entity = {
            "type": "mention",
            "text": f"<at>{self.mention_display_name}</at>",
            "mentioned": {
                "id": self.mention_uid,
                "name": self.mention_display_name
            }
        }
        adaptive_card_content = {
            "type": "AdaptiveCard",
            "body": [
                {"type": "TextBlock", "text": f"{city}", "size": "large", "weight": "bolder", "style": "heading"},
                {"type": "TextBlock", "text": f"{warning} : {status}", "size": "medium", "weight": "bolder", "spacing": "none"},
                {"type": "TextBlock", "text": f"{obs} {dt} 発表", "spacing": "none"},
                {"type": "TextBlock", "text": f"{mention_entity['text']}", "spacing": "none"}
            ],
            "actions": [
                { "type": "Action.OpenUrl", "title": f"気象庁｜{JMAWebURLs.getLink(city)[0]}の警報・注意報を開く", "url": f"{JMAWebURLs.getLink(city)[1]}", "role": "button"}
            ],
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.0",
            "msteams": {"entities": [mention_entity]}
        }
        self.teams.payload = {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": adaptive_card_content
            }]
        }

    def send_message(self, obs, city, warning, status, dt):
        self.__create_mention_payload(obs, city, warning, status, dt)
        self.teams.send()