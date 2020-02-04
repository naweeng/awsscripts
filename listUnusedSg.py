#!/usr/bin/env python
import boto3
import boto
from boto import ec2


def getRegions():
    ec2 = boto3.client('ec2', region_name='us-east-1')
    region = []
    response = ec2.describe_regions()
    regions = response['Regions']
    for r in regions:
        region.append(r['RegionName'])

    return sorted(region)

def listDbSgs(region):
    dbSgDict = {}
    db = boto3.client('rds', region_name=region)
    response = db.describe_db_instances()['DBInstances']
    for db in response:
        if len(db['VpcSecurityGroups']) > 0:
            sgList = []
            sgs = db['VpcSecurityGroups']
            for sg in sgs:
                sgList.append(sg['VpcSecurityGroupId'])
            dbSgDict[db['DBInstanceIdentifier']] = sgList
    return dbSgDict


def listLbSgs(region):
    lbDict = {}
    elb = boto3.client('elb', region_name=region)
    alb = boto3.client('elbv2', region_name=region)
    response_elb = elb.describe_load_balancers()['LoadBalancerDescriptions']
    response_alb = alb.describe_load_balancers()['LoadBalancers']
    response = response_elb + response_alb
    for lb in response:
        lbDict[lb['LoadBalancerName']] = lb['SecurityGroups']
    return lbDict

def listSgs(region):
    sgList = []
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_security_groups()['SecurityGroups']
    for sg in response:
        print sg
        ruleList = []
        sgrules = sg['IpPermissions']
        for r in sgrules:
            r_item = {
                'FromPort': r['FromPort'] if 'FromPort' in r else 'None',
                'IpRanges': [i['CidrIp'] for i in r['IpRanges']],
                'ToPort': r['ToPort'] if 'ToPort' in r else 'None',
                'Proto': r['IpProtocol']
            }
            ruleList.append(r_item)
        sg_item = {
            'Id': sg['GroupId'],
            'VpcId': sg['VpcId'] if 'VpcId' in sg else 'None',
            'GroupName': sg['GroupName'],
            'Tags': sg['Tags'] if 'Tags' in sg else 'None',
            'Rules': ruleList
        }
        sgList.append(sg_item)
    return sgList

def listUnusedSg(region):
    list_of_sg = []
    if region != 'eu-west-3':
        conn = ec2.connect_to_region(region)
        sg = conn.get_all_security_groups()
        for securityGroup in sg:
            if len(securityGroup.instances()) == 0:
                if securityGroup.name != "default":
                    #connection.delete_security_group(group_id=securityGroup.id)
                    list_of_sg.append(securityGroup.id)
    return list_of_sg

regions = getRegions()
print regions
# regions = ['ap-northeast-1', 'ap-northeast-2', 'ap-south-1', 'ap-southeast-1', 'ap-southeast-2', 'ca-central-1', 'eu-central-1',
#     'eu-west-1', 'eu-west-2', 'sa-east-1', 'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']
for r in regions:
    DbSgs = listDbSgs(r)
    # print DbSgs
    DbSgList = []
    for sgList in DbSgs.itervalues():
        for sg in sgList:
            DbSgList.append(sg)
    # print "DBSGLIST:",DbSgList
    lbSgs = listLbSgs(r)
    lbSgList = []
    for sgList in lbSgs.itervalues():
        for sg in sgList:
            lbSgList.append(sg)
    # print "LBSGLIST:",lbSgList
    unused_sgs = listUnusedSg(r)
    print r
    print "----------------------------------"
    for sg in unused_sgs:
        if sg not in lbSgList and sg not in DbSgList:
            print sg
    print "-----*************************-----"
