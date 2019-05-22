#!/usr/bin/env python3
import boto3
import argparse

def get_instance_details():
    spot_instance_list = []
    ec2 = boto3.resource('ec2', region_name=awsRegion)

    instances = ec2.instances.filter(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']},
            {'Name': 'tag:Name', 'Values': [instanceTagName]},
            {'Name': 'instance-lifecycle', 'Values': ['spot']}
        ]
    )
    for instance in instances:
        spot_instance_list.append(instance.instance_id)
    return spot_instance_list

def get_alarm_details(nameFilter):
    alarm_list = []
    cw = boto3.client('cloudwatch', region_name=awsRegion)
    paginator = cw.get_paginator('describe_alarms')
    for response in paginator.paginate():
        for alarm in response['MetricAlarms']:
            if nameFilter in alarm['AlarmName']:
                alarm_instance = {
                    'AlarmName': alarm['AlarmName'],
                    'InstanceId': alarm['Dimensions'][0]['Value']
                }
                alarm_list.append(alarm_instance)
    return alarm_list

def create_cloudwatch_alarm(id):
    cw = boto3.client('cloudwatch', region_name=awsRegion)
    response = cw.put_metric_alarm(
        AlarmName=alarmNamePattern + ' ' + str(id),
        ComparisonOperator='LessThanThreshold',
        EvaluationPeriods=12,
        MetricName='CPUUtilization',
        Namespace='AWS/EC2',
        Period=300,
        Statistic='Average',
        Threshold=cpuThreshold,
        AlarmActions=[
            'arn:aws:swf:' + awsRegion + ':' + accountId + ':action/actions/AWS_EC2.InstanceId.Terminate/1.0'
        ],
        AlarmDescription='Terminate when spot cpu utilization drops below ' + str(cpuThreshold) + '% for ' + str(id),
        Dimensions=[
            {
              'Name': 'InstanceId',
              'Value': id
            },
        ],
        Unit='Percent'
    )
    return response

def delete_unused_alarms(nameFilter):
    cw = boto3.client('cloudwatch', region_name=awsRegion)
    for alarm in get_alarm_details(nameFilter):
        if alarm['InstanceId'] not in get_instance_details():
            print(alarm['InstanceId'] + ' is not running.So removing the alarm ' + alarm['AlarmName'])
            cw.delete_alarms(
                AlarmNames=[alarm['AlarmName']]
            )
        else:
            print(alarm['InstanceId'] + ' is running. So not removing the alarm ' + alarm['AlarmName'])



# Vars Decalaration/Initialization
parser = argparse.ArgumentParser()
parser.add_argument(dest='awsRegion')
parser.add_argument(dest='alarmNamePattern')
parser.add_argument(dest='instanceTagName')
parser.add_argument(dest='accountId')
parser.add_argument(dest='cpuThreshold')
args = parser.parse_args()
awsRegion=args.awsRegion
alarmNamePattern=args.alarmNamePattern
instanceTagName=args.instanceTagName
accountId=args.accountId
cpuThreshold=int(args.cpuThreshold)


# Print all alarms before the script runs
print("Pre Run")
for alarm in get_alarm_details(alarmNamePattern):
    print(alarm)
print("------------------------------------------------")

# Delete unused alarms
delete_unused_alarms(alarmNamePattern)

# Create alarms for spot instances
for i in get_instance_details():
    create_cloudwatch_alarm(i)


# Print all alarms after the script runs
print("Post Run")
for alarm in get_alarm_details(alarmNamePattern):
    print(alarm)
print("------------------------------------------------")
