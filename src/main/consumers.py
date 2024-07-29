from django.template.loader import get_template
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

class CheerEventConsumer(WebsocketConsumer):
    
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["user_id"]
        
        async_to_sync(self.channel_layer.group_add)(
            self.room_name, self.channel_name
        )
        
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_name, self.channel_name
        )

    def play_sfx(self, event):
        template_name = "overlay/partials/sfx_player.html"
        html = get_template(template_name).render(
            context = {
                "sfx_source": event["sfx_source"]
            }
        )
        self.send(text_data=html)