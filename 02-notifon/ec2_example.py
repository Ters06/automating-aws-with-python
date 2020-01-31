# coding: utf-8
import boto3
session = boto3.Session(profile_name='pythonAutomation')
ec2 = session.resource('ec2')
key_name = 'python_automation_key'
key_path = key_name + '.pem'
key = ec2.create_key_pair(KeyName=key_name)
key.key_material
with open(key_path, 'w') as key_file:
    key_file.write(key.key_material)
    
get_ipython().run_line_magic('ls', '-l python_automation_key.pem')
import os, stat
os.chmod (key_path, stat.S_IRUSR | stat.S_IWUSR)
get_ipython().run_line_magic('ls', '-l python_automation_key.pem')
ec2.images.filter(Owners=['amazon'])
len(list(ec2.images.filter(Owners=['amazon'])))
len(list(ec2.images.filter(Owners=['amazon'])))
img = ec2.Image('ami-007fae589fdf6e955')
img.name
ami_name = 'amzn2-ami-hvm-2.0.20191217.0-x86_64-gp2'
filters = [{'Name': 'name', 'Values': [ami_name]}]
list(ec2.images.filter(Owners=['amazon'], Filters=filters))
instances = ec2.create_instances(ImageId=img.id, MinCount=1, MaxCount=1, InstanceType='t2.micro', KeyName=key.key_name)
instances[0].terminate()
instances = ec2.create_instances(ImageId=img.id, MinCount=1, MaxCount=1, InstanceType='t2.micro', KeyName=key.key_name)
inst = instances[0]
inst.public_dns_name
inst.public_dns_name
inst.public_dns_name
inst.wait_until_running()
inst.reload()
inst.public_dns_name
inst.security_groups
sg = inst.security_groups[0]
security_group = ec2.SecurityGroup(sg['GroupId'])
security_group
security_group.authorize_ingress(
    CidrIp='81.240.173.206',
    FromPort=22,
    GroupName=sg['GroupName'],
    IpProtocol='TCP',
    ToPort=22
    )
security_group.authorize_ingress(
    CidrIp='81.240.173.206/32',
    FromPort=22,
    GroupName=sg['GroupName'],
    IpProtocol='TCP',
    ToPort=22
    )
security_group.authorize_ingress(
    CidrIp='0.0.0.0/0',
    FromPort=80,
    GroupName=sg['GroupName'],
    IpProtocol='TCP',
    ToPort=80
    )
inst.public_dns_name
get_ipython().run_line_magic('history', '')
