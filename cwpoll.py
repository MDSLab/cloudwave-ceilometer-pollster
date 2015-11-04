# Copyright 2014 University of Messina (UniMe)
#
# Author: Nicola Peditto <npeditto@unime.it>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# -*- encoding: utf-8 -*-
#
# Author: Nicola Peditto <npeditto@unime.it>
#
#
import ceilometer
from ceilometer import sample
from ceilometer.compute import plugin
from ceilometer.compute.pollsters import util
from ceilometer.compute.virt import inspector as virt_inspector
from ceilometer.openstack.common import log

import json
from oslo.config import cfg
import pika


LOG = log.getLogger(__name__)


cwpoll_opts = [
    cfg.StrOpt('amqp_compute_ip',
               default=None,
               help='AMQP compute IP address'),

    cfg.StrOpt('amqp_compute_port',
               default=None,
               help='AMQP compute PORT address'),

]

cfg.CONF.register_opts(cwpoll_opts, group='cloudwave')




class CwPollster(plugin.ComputePollster):

    
    def callback(self, ch, method, properties, body):

        LOG.info('CW -> Start Consumer Callback:')

	self.messages = self.messages + 1
        LOG.info('CW -> Message NUMBER %s', self.messages)

	LOG.info('CW -> Meter dequeued:\n%s\n', body)
	self.message_list.append(body)

	if self.messages == self.q_len:

       	        LOG.info('CW -> Queue is now EMPTY!')
                ch.stop_consuming()
           	#self.connection.close()
               	LOG.info('CW -> STOP consuming!!!!!!!!!!!!!!!!!!')





    def get_samples(self, manager, cache, resources):

	for self.instance in resources:

            	#LOG.debug(_('checking instance %s'), self.instance.id)
            	#instance_name = util.instance_name(instance)

		LOG.info("\n\n------------------------------!!!!!! CloudWave Pollster START !!!!!!------------------------------\n\n")
        	instance_name = getattr(self.instance, 'id', None) #util.instance_name(instance)
	
		LOG.debug('CW -> Instance Host %s', getattr(self.instance, 'OS-EXT-SRV-ATTR:host', None))
		#LOG.debug(str(dir(instance)))

        	LOG.info("CW -> INSTANCE: %s", self.instance)

		LOG.info('CW -> Checking CloudWave instance %s', instance_name)



		try:

                        #Ceilometer sample variables
                        METER_name = ""
                        METER_volume = ""
                        METER_metadata = ""
                        METER_unit = ""
                        METER_type = ""

		  
			self.message_list=[]
			self.messages = 0

			queue = "CloudWave."+instance_name
			routing_key=queue
			
                        credentials = pika.PlainCredentials('guest', 'guest')	#credentials = pika.PlainCredentials('username', 'password')
                        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', credentials=credentials))

			channel = self.connection.channel()
			channel.exchange_declare(exchange='CloudWave', type='topic')

			self.result = channel.queue_declare(queue=queue, durable=False, exclusive=False, auto_delete=False)
			self.q_len = self.result.method.message_count
			queue_name = self.result.method.queue
                        channel.queue_bind(exchange="CloudWave", queue=queue_name, routing_key=routing_key)


			LOG.info('CW -> START Consuming - %s message/s ', self.q_len)

			if self.q_len == 0:

				LOG.info("CW -> NO SAMPLE TO SEND TO CEILOMETER!")
        	      		#self.connection.close()
				LOG.info('CW -> STOP consuming and close connection: Queues are empty!!!')

       			else:

				channel.basic_consume(self.callback, queue=queue_name, no_ack=True)
				channel.start_consuming()
			
				for msg in self.message_list:
					
					#LOG.info('\nCW -> Meter dequeued %s', str(msg))
					
			        	j = json.loads(msg)
        				METER_name = j['name']
        				METER_volume = j['volume']
			        	METER_metadata = j['additional_metadata']    #e.g.: {'geo_meter':'coord' }
			        	METER_unit = j['unit']
       			 		METER_type = j['type']
        
					
                        		LOG.info('CW -> METER_name %s', METER_name)
					
                        		yield util.make_sample_from_instance(
                                			self.instance,
                                			name = METER_name,
                                			type = sample.TYPE_GAUGE,
                                			unit = METER_unit,
                               	 			volume = METER_volume,
                                			additional_metadata = METER_metadata,
                        		)       
                
                        		LOG.info("CW -> SAMPLE CREATED!")
					



       		except Exception as err:
            		LOG.error('CW -> could not get METERS for %s: %s', self.instance.id, err)
            		LOG.exception(err)


		LOG.info("\n\n------------------------------!!!!!! CloudWave Pollster STOP !!!!!!------------------------------\n\n")
