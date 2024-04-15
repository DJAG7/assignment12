import boto3

ec2_client = boto3.client('ec2')
asg_client = boto3.client('autoscaling')
elbv2_client = boto3.client('elbv2')

# AWS Configuration
vpc_id = 'vpc-05b7ee416d26d6fde'
subnet_ids = ['subnet-0f81a0dc61ffab786', 'subnet-01f0b5df71193dd9d']  # Subnets in eu-west-2a and eu-west-2b
security_group_id = 'sg-0001c611016f1a11b'
key_pair_name = 'daniel-mern'
image_id = 'ami-0b9932f4918a00c4f'  # Ubuntu AMI

# Data script
user_data_script = """#!/bin/bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker

# Pull and run Docker containers from ECR
sudo docker run -d -p 80:80 --restart always public.ecr.aws/s7f2n3x3/danielmerncontainers:latest
sudo docker run -d -p 3001:3001 --restart always public.ecr.aws/s7f2n3x3/danielmerncontainers@sha256:cc4283902cf022a553f40ce545d0fc467ab1b761111f3e916b0411e4996442e8
sudo docker run -d -p 3002:3002 --restart always public.ecr.aws/s7f2n3x3/danielmerncontainers@sha256:9903bbe46a904247bcba14984bf8ec17615c86054effc06c20e5d76e340c2569
"""

# Create a Launch Configuration
def create_launch_configuration():
    asg_client.create_launch_configuration(
        LaunchConfigurationName='daniel-mern-launch-configuration',
        ImageId=image_id,
        KeyName=key_pair_name,
        SecurityGroups=[security_group_id],
        InstanceType='t2.micro',
        UserData=user_data_script
    )
    print("Launch Configuration created.")

# Create Load Balancer and Target Group
def create_load_balancer_and_target_group():
    # Create an Application Load Balancer
    alb_response = elbv2_client.create_load_balancer(
        Name='daniel-mern-load-balancer-main',
        Subnets=subnet_ids,
        SecurityGroups=[security_group_id],
        Scheme='internet-facing',
        Tags=[{'Key': 'Name', 'Value': 'MyALB'}]
    )
    alb_arn = alb_response['LoadBalancers'][0]['LoadBalancerArn']
    print("Application Load Balancer created:", alb_arn)

    # Create a target group for HTTP traffic on port 80
    tg_response = elbv2_client.create_target_group(
        Name='daniel-mern-target-group-main',
        Protocol='HTTP',
        Port=80,
        VpcId=vpc_id,
        HealthCheckProtocol='HTTP',
        HealthCheckPort='80',
        HealthCheckPath='/',
        HealthCheckIntervalSeconds=30,
        HealthCheckTimeoutSeconds=5,
        HealthyThresholdCount=5,
        UnhealthyThresholdCount=2,
        Matcher={'HttpCode': '200'}
    )
    target_group_arn = tg_response['TargetGroups'][0]['TargetGroupArn']
    print("Target Group created:", target_group_arn)

    return alb_arn, target_group_arn

# Create Auto Scaling Group with Load Balancer
def create_auto_scaling_group(alb_arn, target_group_arn):
    asg_client.create_auto_scaling_group(
        AutoScalingGroupName='daniel-mern-asg-main',
        LaunchConfigurationName='daniel-mern-launch-configuration',
        MinSize=1,
        MaxSize=3,
        DesiredCapacity=2,
        VPCZoneIdentifier=','.join(subnet_ids),
        TargetGroupARNs=[target_group_arn],
        Tags=[{
            'ResourceType': 'auto-scaling-group',
            'Key': 'Name',
            'Value': 'Daniel-Mern',
            'PropagateAtLaunch': True
        }]
    )
    print("Auto Scaling Group created.")


# Integrate all steps to setup the infrastructure
def setup_infrastructure():
    create_launch_configuration()
    alb_arn, target_group_arn = create_load_balancer_and_target_group()
    create_auto_scaling_group(alb_arn, target_group_arn)

setup_infrastructure()
