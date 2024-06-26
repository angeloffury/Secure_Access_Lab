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
        instance_tag=instance['Tags'][0]
        ec2_client.start_instances(InstanceIds=[instance['InstanceId']])
        print("\t\t",instance_tag['Value']," ec2 started.")
        '''
        print("\t\t",instance_tag['Value']," ec2 started. Please wait! It may take upto 30-60 sec to complete...")
        instance_runner_waiter = ec2_client.get_waiter('instance_running')
        instance_runner_waiter.wait(InstanceIds=[instance['InstanceId']])
        waiter = ec2_client.get_waiter('instance_running')
       
         waiter.wait(
            InstanceIds=[instance['InstanceId']]
            )
        print("\t\tClient",i," ec2 is RUNNING.")
        '''
        i+=1
    print("\n\tVerify the ec2 instances are RUNNING in the AWS console. Each instance may take upto 30-60 sec to complete...")
    return 

def stop_ec2_instances(ec2_client,ec2_instances):
    i=1
    for instance in ec2_instances: 
        instance_tag=instance['Tags'][0]
        print("\t\t",instance_tag['Value']," ec2 requested to stop. Please wait! It may take upto 30-60 sec to complete...")
        ec2_client.stop_instances(InstanceIds=[instance['InstanceId']])
        waiter = ec2_client.get_waiter('instance_stopped')
        waiter.wait(Filters=[{'Name': 'instance-state-name','Values': ['stopped']}])
        waiter = ec2_client.get_waiter('instance_stopped')
        waiter.wait(
            InstanceIds=[instance['InstanceId']]
            )
        print("\t\t",instance_tag['Value']," ec2 is STOPPED.")
        i+=1
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
            instance_tags = instance['Tags'][0]
            if(block_device_mapping != []):
                for volId in block_device_mapping:
                    volume_id = volId['Ebs']['VolumeId']
                    print ("\t\t("+str(i)+"a)Trying to DETACH ",instance_tags['Value'], "'s Volume. Please wait...")
                    response=detach_ebs_volume(ec2_client, instance_id, volume_id)
                    print("\t\t   Storage of ",instance_tags['Value']," is DETACHED.")
                    print ("\t\t("+str(i)+"b)Trying to DELETE ",instance_tags['Value'], "'s Volume. Please wait...")
                    delete_ebs_volume(ec2_client,volume_id)
                    print("\t\t   Storage of ",instance_tags['Value']," is DELETED.")
                    name=instance_tags['Value']+"-golden"
                    Snapshots=ec2_client.describe_snapshots(Filters=[{'Name':'tag:Name','Values':[name]},],OwnerIds=['self'])
                    for snapshot in Snapshots['Snapshots']:
                        print ("\t\t("+str(i)+"c)Trying to CREATE ",instance_tags['Value'], "'s new Volume. Please wait...")
                        response =create_volume_from_snapshot(ec2_client,snapshot['SnapshotId'],instance_tags['Value'])
                        print ("\t\t   CREATED new volume for ",instance_tags['Value'])
                        print ("\t\t("+str(i)+"d)Trying to ATTACH ",instance_tags['Value'], "'s new Volume. Please wait...")
                        attach_volume(ec2_client,response['VolumeId'],instance_id)
                        print ("\t\t   ATTACHED new volume to ",instance_tags['Value'])

            else:
                name=instance_tags['Value']+"-golden"
                Snapshots=ec2_client.describe_snapshots(Filters=[{'Name':'tag:Name','Values':[name]},],OwnerIds=['self'])
                for snapshot in Snapshots['Snapshots']:
                    print ("\t\t("+str(i)+"a)Trying to CREATE ",instance_tags['Value'], "'s new Volume. Please wait...")
                    response =create_volume_from_snapshot(ec2_client,snapshot['SnapshotId'],instance_tags['Value'])
                    print ("\t\t   CREATED new volume for ",instance_tags['Value'])
                    print ("\t\t("+str(i)+"b)Trying to ATTACH ",instance_tags['Value'], "'s new Volume. Please wait...")
                    attach_volume(ec2_client,response['VolumeId'],instance_id)
                    print ("\t\t   ATTACHED new volume to ",instance_tags['Value'])
            i+=1
            print()
    
    except Exception as ERR:
        print(ERR)
        exit()
       
def delete_snapshot_by_name(ec2_client,snapshot_name):
    """
    Deletes an AWS snapshot with a specific name.
    """
    try:
        
        # Get list of available snapshots
        response = ec2_client.describe_snapshots(Filters=[{'Name': 'tag:Name', 'Values': [snapshot_name]}])

        # Iterate over snapshots with the specified name
        for snapshot in response['Snapshots']:
            snapshot_id = snapshot['SnapshotId']

            # Delete the snapshot
            ec2_client.delete_snapshot(SnapshotId=snapshot_id)
            print(f"\tDELETED snapshot of", snapshot_name)
    
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    

def get_volume_ids_by_ec2_name(ec2_client, aws_client_name):
    """
    Get volume IDs associated with an EC2 instance using its name tag.
    """
    try:

        # Get the instance IDs by searching for instances with the specified name tag
        response = ec2_client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [aws_client_name]}])

        # Extract volume IDs associated with the instances
        volume_ids = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                for volume in instance['BlockDeviceMappings']:
                    volume_ids.append(volume['Ebs']['VolumeId'])

        number_of_volume_ids=len(volume_ids)
        if(number_of_volume_ids==1):
            return volume_ids[0]
        elif (number_of_volume_ids==0):
            raise("No Volume IDs found. Please check AWS Instance.")
        else:
            raise("More than 1 Volume IDs found. Please check AWS Instance")
    except Exception as e:
        print(f"\tAn error occurred: {e}")
        return []



def create_snapshot(ec2_client,volume_id, snapshot_name, snapshot_description):
    """
    Creates an AWS snapshot with a specific name and description.
    """
    try:

        # Create the snapshot
        response = ec2_client.create_snapshot(
            VolumeId=volume_id,
            Description=snapshot_description,
            TagSpecifications=[
                {
                    'ResourceType': 'snapshot',
                    'Tags': [
                        {'Key': 'Name', 'Value': snapshot_name},
                    ]
                },
            ]
        )

        snapshot_id = response['SnapshotId']
        print(f"\tCREATED new Golden image for",snapshot_name)
        return snapshot_id
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

