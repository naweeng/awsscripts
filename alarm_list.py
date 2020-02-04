#!/usr/bin/python
import os
import boto3
from datetime import datetime,timedelta
import argparse

ec2 = boto3.client('ec2', region_name='us-east-1')

# Get all regions of AWS
def get_regions():
    response = ec2.describe_regions()
    regions = [ region['RegionName'] for region in response['Regions']]
    return regions

# Get InstanceId, InstanceName and Status of all instances in a given region
def get_instances(region):
    instance_list = []
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_instances()
    for r in response['Reservations']:
        for i in r['Instances']:
            instanceId = i['InstanceId']
            tags = i['Tags']
            for t in tags:
                if t['Key'] == 'Name':
                    instanceName = t['Value']
                # else:
                #     instanceName = 'Not Defined'
            instanceState = i['State']['Name']
            instance = {'id': instanceId, 'name': instanceName, 'state': instanceState}
            instance_list.append(instance)
    return instance_list

# Get status_failed details for a given instance_id for a duration of startdate - enddate
def get_status_failed(startdate,enddate,instance_id):
    positive_instance_ids = {}
    positive_instance_ids[instance_id] = 0   
    client = boto3.client('cloudwatch', region_name=region)
    counter = str((enddate - startdate)/5).split(' ',1)[0]
    for i in range(int(counter), -1, -1):
        curr_start_date = startdate
        if (curr_start_date + timedelta(days=4) < enddate):
            curr_end_date = curr_start_date + timedelta(days=5)
        else:
            curr_end_date = enddate + timedelta(days=1)
        # print curr_start_date,curr_end_date
        response = client.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='StatusCheckFailed',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': instance_id
                },
            ],
            StartTime=curr_start_date,
            EndTime=curr_end_date,
            Period=300,
            Statistics=['Average']
        )
        # print "Data for the range " + str(curr_start_date) + " - " + str(curr_end_date)
        for data in response['Datapoints']:
            if data['Average'] != 0.0:
                # print data
                positive_instance_ids[instance_id] = positive_instance_ids[instance_id] + 1
        startdate = curr_end_date
    positive_instances = {k:v for (k,v) in positive_instance_ids.iteritems() if v != 0}
    return positive_instances



parser = argparse.ArgumentParser()
parser.add_argument(dest='startdate')
parser.add_argument(dest='enddate')
args = parser.parse_args()
startdate = datetime.strptime(args.startdate, '%Y-%m-%d')
enddate = datetime.strptime(args.enddate, '%Y-%m-%d')
# Get instances from all regions
for region in ['us-east-2', 'us-west-1', 'us-west-2', 'us-east-1']:#get_regions():
    print 'Working on ' + region
    instances = get_instances(region)
    # print instances
    for i in instances:
        # print 'Details for (' + i['id'] + ') ' + i['name'] + ' instance'
        print i['name'],get_status_failed(startdate,enddate,i['id'])
        
