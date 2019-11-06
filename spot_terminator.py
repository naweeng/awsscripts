#!/usr/bin/env python3
import boto3
import os
from datetime import datetime,timedelta,timezone

def sns_invoke(msg):
    sns = boto3.client('sns', region_name=awsRegion)
    response = sns.publish(
        TopicArn='arn:aws:sns:' + awsRegion + ':' + accountId + ':' + snsTopic,
        Message=msg,
    )

def terminate_instances(instance_list):
    eclient = boto3.client('ec2', region_name=awsRegion)
    waiter = eclient.get_waiter('instance_terminated')
    ec2 = boto3.resource('ec2', region_name=awsRegion)
    ec2.instances.filter(Filters=[{'Name': 'instance-id', 'Values': instance_list},{'Name': 'instance-lifecycle', 'Values': ['spot']}]).terminate()
    # waiter.wait(InstanceIds = instance_list)

# Get all running spot instances with matching tagname that were launched atleast an hour ago.
def get_instance_details():
    print(instanceTagName)
    spot_instance_list = []
    ec2 = boto3.resource('ec2', region_name=awsRegion)

    instances = ec2.instances.filter(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']},
            {'Name': 'tag:Name', 'Values': instanceTagName},
            {'Name': 'instance-lifecycle', 'Values': ['spot']}
        ]
    )
    for instance in instances:
        if ((datetime.now(timezone.utc) - instance.launch_time).seconds/5400) > 0:
            spot_instance_list.append(instance.instance_id)
    return spot_instance_list

def get_metric_statistics(id,startTime,endTime):
    statistic_list = []
    client = boto3.client('cloudwatch', region_name=awsRegion)
    response = client.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        Dimensions=[
            {
                'Name': 'InstanceId',
                'Value': id
            },
        ],
        StartTime=startTime,
        EndTime=endTime,
        Period=300,
        Statistics=['Average']
    )
    for data in response['Datapoints']:
        statistic_list.append(data)
    return statistic_list


def threshold_check(stats_list,cpuThreshold):
    for stat in stats_list:
        if stat['Average'] > cpuThreshold:
            return False
    return True


# Vars Decalaration/Initialization
startTime=(datetime.utcnow() - timedelta(hours=1)).isoformat()
endTime=datetime.utcnow().isoformat()
awsRegion=os.environ['AWS_REGION']
accountId=os.environ['ACCOUNT_ID']
snsTopic=os.environ['SNS_TOPIC']
instanceTagName=[i for i in os.environ['INSTANCE_TAG_NAME'].split(" ")]
cpuThreshold=int(os.environ['CPU_THRESHOLD'])


def lambda_handler(event, context):
    instance_to_terminate = []
    for instance in get_instance_details():
        # print(instance)
        stats_list = get_metric_statistics(instance,startTime,endTime)
        if threshold_check(stats_list,cpuThreshold):
            instance_to_terminate.append(instance)

    print('Total spot instances for ' + str(instanceTagName) + ' is ' + str(len(get_instance_details())))
    if len(instance_to_terminate) > 0:
        print('These instances will be terminated ' + str(instance_to_terminate))
        terminate_instances(instance_to_terminate)
        sns_invoke('These instances are terminated' + str(instance_to_terminate))
    else:
        print('Nothing to terminate right now.')
