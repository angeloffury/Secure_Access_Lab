import boto3

def get_ec2_instances(ec2_client,ec2_names):
    instance_subset=[]
    instances=ec2_client.describe_instances(
        Filters=[ {'Name':'tag:Name','Values':ec2_names} ]
    )
    for instance in instances['Reservations']:
        for i in instance["Instances"]:
            instance_subset.append(i)

    return instance_subset

def start_ec2_instances(ec2_client,ec2_instances):
    i=1
    for instance in ec2_instances: 
        ec2_client.start_instances(InstanceIds=[instance['InstanceId']])
        print("\t\tClient",i," ec2 started. Please wait! It may take upto 30-60 sec to complete...")
        instance_runner_waiter = ec2_client.get_waiter('instance_running')
        instance_runner_waiter.wait(InstanceIds=[instance['InstanceId']])
        waiter = ec2_client.get_waiter('instance_running')
        waiter.wait(
            InstanceIds=[instance['InstanceId']]
            )
        print("\t\tClient",i," ec2 is RUNNING.")
        i+=1
    return 

def stop_ec2_instances(ec2_client,ec2_instances):
    i=1
    for instance in ec2_instances: 
        print("\t\tClient",i," ec2 requested to stop. Please wait! It may take upto 30-60 sec to complete...")
        ec2_client.stop_instances(InstanceIds=[instance['InstanceId']])
        waiter = ec2_client.get_waiter('instance_stopped')
        waiter.wait(Filters=[{'Name': 'instance-state-name','Values': ['stopped']}])
        waiter = ec2_client.get_waiter('instance_stopped')
        waiter.wait(
            InstanceIds=[instance['InstanceId']]
            )
        print("\t\tClient",i," ec2 is STOPPED.")
        i+=1
    print()
    return 

def detach_ebs_volume(ec2_client,instance_id,volume_id):
    response = ec2_client.detach_volume(
                        InstanceId=instance_id,
                        VolumeId=volume_id,
                        Force=True
                    )
    waiter = ec2_client.get_waiter('volume_available')
    waiter.wait(VolumeIds=[volume_id])
    return response

def delete_ebs_volume(ec2_client, volume_id):
    ec2_client.delete_volume(
                        VolumeId=volume_id,
                    )
    waiter = ec2_client.get_waiter('volume_deleted')
    waiter.wait(Filters=[{'Name': 'status','Values': ['deleted']},],VolumeIds=[volume_id])


def create_volume_from_snapshot(ec2_client,snapshot_id, volume_name, availability_zone="us-east-2c", volume_type='gp3', volume_size=None):

    # If volume_size is not provided, get the snapshot size
    if volume_size is None:
        snapshot_info = ec2_client.describe_snapshots(SnapshotIds=[snapshot_id])
        volume_size = snapshot_info['Snapshots'][0]['VolumeSize']

    # Create the tags for the volume
    tags = [{'Key': 'Name', 'Value': volume_name}]

    # Create the new volume from the snapshot
    response = ec2_client.create_volume(
        SnapshotId=snapshot_id,
        AvailabilityZone=availability_zone,
        VolumeType=volume_type,
        Size=volume_size,
        TagSpecifications=[{'ResourceType': 'volume', 'Tags': tags}]
    )
    waiter = ec2_client.get_waiter('volume_available')

    # Wait until the volume is available
    waiter.wait(
        VolumeIds=[response['VolumeId']]
    )

    return response

def attach_volume(ec2_client,volume_id, instance_id, device_name = '/dev/sda1'):
    
    # Attach the volume to the instance
    response = ec2_client.attach_volume(
        Device=device_name,
        InstanceId=instance_id,
        VolumeId=volume_id
    )

    return response


def reset_ec2_volumes(ec2_client,ec2_instances):
    try:
        i=1
        for instance in ec2_instances:
            block_device_mapping=instance['BlockDeviceMappings']
            instance_id=instance['InstanceId']
            if(block_device_mapping != []):
                for volId in block_device_mapping:
                    volume_id = volId['Ebs']['VolumeId']
                   
                    print ("\t\t("+str(i)+"a)Trying to DETACH Client",i, "'s Volume. Please wait...")
                    response=detach_ebs_volume(ec2_client, instance_id, volume_id)
                    print("\t\t   Storage of Client",i," is DETACHED.")
                    print ("\t\t("+str(i)+"b)Trying to DELETE Client",i, "'s Volume. Please wait...")
                    delete_ebs_volume(ec2_client,volume_id)
                    print("\t\t   Storage of Client",i," is DELETED.")
                    description = "win11-client"+str(i)
                    Snapshots=ec2_client.describe_snapshots(Filters=[{'Name': 'description','Values': [description]},],OwnerIds=['self'])
                    for snapshot in Snapshots['Snapshots']:
                        print ("\t\t("+str(i)+"c)Trying to CREATE Client",i, "'s new Volume. Please wait...")
                        response =create_volume_from_snapshot(ec2_client,snapshot['SnapshotId'],description)
                        print ("\t\t   CREATED new volume for Client",i)
                        print ("\t\t("+str(i)+"d)Trying to ATTACH Client",i, "'s new Volume. Please wait...")
                        attach_volume(ec2_client,response['VolumeId'],instance_id)
                        print ("\t\t   ATTACHED new volume to Client",i)
            i+=1
            print()
    
    except Exception as ERR:
        print(ERR)
        exit()
       

