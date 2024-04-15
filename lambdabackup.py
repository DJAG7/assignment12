import boto3

def lambda_handler(event, context):
    # Initializing Client
    ec2 = boto3.client('ec2')
    asg = boto3.client('autoscaling')

    # AutoScaling Group
    asg_name = 'daniel-mern-asg-main'

    # Generating List from ASG
    asg_response = asg.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
    instance_ids = [instance['InstanceId'] for instance in asg_response['AutoScalingGroups'][0]['Instances']]

    #backing up each instance
    for instance_id in instance_ids:
        # creating snapshots for the instances
        volumes = ec2.describe_volumes(Filters=[{'Name': 'attachment.instance-id', 'Values': [instance_id]}])
        for volume in volumes['Volumes']:
            volume_id = volume['VolumeId']
            snapshot = ec2.create_snapshot(VolumeId=volume_id, Description=f"Backup of {volume_id}")
            print(f"Created snapshot: {snapshot['SnapshotId']}")

    return {
        'statusCode': 200,
        'body': 'Snapshot process completed successfully.'
    }
