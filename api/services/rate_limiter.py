import time
import logging
import threading


logger= logging.getLogger(__name__)


class Ratelimiter():
    def __init__(self,req_per_min:int,):
        logger.info("Ratelimiter inicializado")
        self.req_per_min = req_per_min
        self.max = req_per_min
        self.refill_rate = req_per_min/60
        self.tokens= req_per_min
        self.last_refill = time.time()
        self.timeout=  (60 / req_per_min) * 2
        #lock para race condition
        self.lock= threading.Lock()
        
        pass    
    

    def allow_request(self):
        start= time.time()     
        while True:
            #tiempo actual
         with self.lock:
            now= time.time()
            elapsed_time= now-self.last_refill
            tokens_to_add= elapsed_time*self.refill_rate
            self.tokens=min(self.max,self.tokens+tokens_to_add)
            self.last_refill=now
         
            if self.tokens>=1:
                self.tokens-=1
        
                return True
                
            else:
                missing_time= (1-self.tokens)/self.refill_rate
                if missing_time>0.5:
                  logger.debug(f"esperando {missing_time} para obtener token")

         if now-start>self.timeout:
                    return False 
         time.sleep(0.1)



def worker_test(ratelimiter:Ratelimiter):
  for i in range(10):
     result=ratelimiter.allow_request()
     if not result:
         print("TIMEOUT!")
     if result:
         print(f"WORKER {threading.current_thread().name}\nHORA: {time.strftime('%H:%M:%S')}\nTOKENS: {ratelimiter.tokens}\nITERACION: {i}")
         time.sleep(0.1)
     
def Thread_test(ratelimiter:Ratelimiter):
   th=[]
   for i in range(5):
      thread= threading.Thread(target=worker_test,args=(ratelimiter,))
      th.append(thread)
   for t in th:
         t.start()
   for t in th:
         t.join()
      
if __name__=='__main__':
    rt= Ratelimiter(10)
    Thread_test(rt)
    
