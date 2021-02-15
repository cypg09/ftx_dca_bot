import json
import traceback
from threading import Thread
from numpy import trunc
from time import time, sleep


class DcaBot(Thread):
    def __init__(self,
                 tglog,
                 name,
                 client,
                 frequency: int, # time in seconds between two investments
                 order_size: float,
                 symbol, side, quantity):
        self.alive, self.active = True, True
        self.tglog = tglog
        self.name = name
        self.client = client
        self.frequency = frequency
        self.order_size = order_size
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.total_involved = 0
        self.first_quantity = self.quantity
        self.last_time = 0
        self.handle_order()


    def _client_log(self, text):
        with open(f'{self.name}_log.txt', w) as log:
            log.write(f"\n{text}")
        return

    
    def _pourcent_involvment(self):
        _pourcent = 100 * self.total_involved / self.first_quantity
        return trunc(_pourcent)


    def _is_time_to_order(self):
        now = trunc(time())
        if now > self.last_time + self.frequency:
            self.last_time = now
            return True
        else:
            return False


    def _place_order(self, count=5):
        try:
            jresponse = self.client.place_order("market"=self.symbol,
                                           "side"=self.side,
                                           "price"=None,
                                           "type"="market",
                                           "size"=self.order_size)
            response = json.loads(jresponse)
            if response['success']:
                self._client_log(f"New order placed !\n{response}")
                self.total_involved += self.order_size
                self.quantity -= self.order_size
                if self.quantity < self.order_size:
                    return True
            elif count > 0:
                return self._place_order(count-1)
            else:
                self.tglog.error(f"Handling error causing death: {response}")
                return True
        except:
            self.tglog.error("Error handling in _place_order\n"
                            f"Infos: client={self.name}, symbol={self.symbol},\n"
                            f"quantity={self.quantity}, total_involved={self.total_involved}\n"
                            f"{traceback.format_exc()")
            if count > 0:
                return self._place_order(count-1)
            else:
                self.tglog.error(f"Handling error causing death: {response}")
                return True


    def handle_order(self):
        if self._is_time_to_order():
            _has_ended = self._place_order()
            self.tglog.info(f"Order placed for {self.name}:\n"
                       f"side = {self.side},\n"
                       f"quote_quantity = {self.order_size},\n"
                       f"pourcent_involved = {self._pourcent_involvment()}")
            return _has_ended
        return


    def handle_death(self):
        self.alive = False
        self.tglog.info(f"Client {self.name} got a bot killed on {self.symbol},\n"
                        f"invested {self._pourcent_involvment()}")
        return


    def run(self):
        while self.alive:
            sleep(5*60)
            while not self.active:
                sleep(60)
            if not self.alive:
                break
            has_ended = self.handle_order()
            if has_ended:
                break
            else:
                continue
        self.handle_death()

