# cloudwave-pollster
Openstack Ceilometer Pollster for the EU project CloudWave.

The CW Pollster is an OpenStack Ceilometer pollster used in the Y1 and Y2 that is periodically executed by the OpenStack Ceilometer Agent (running on an OpenStack compute node) to collect measurements and events coming from CW Probes running within CW virtual machines. The CW Pollster launches an AMQP broker whose queues are filled with messages coming from the CW Probes. Periodically the CW Pollster empties the queues and sends messages to the Ceiloesper Dispatcher.
