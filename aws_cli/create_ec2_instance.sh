#!/bin/bash

# Variables
REGION="ap-east-1"  # Hong Kong region
INSTANCE_TYPE="t3.micro"
KEY_NAME="aws224"
SECURITY_GROUP_NAME="aws224"
PEM_FILE="${KEY_NAME}.pem"
AMI_ID="ami-01412724cbc6252ef"  # Updated Ubuntu 22.04 LTS AMI for ap-east-1
VOLUME_SIZE=25

# Create a key pair
aws ec2 create-key-pair --key-name $KEY_NAME --query 'KeyMaterial' --output text > $PEM_FILE
chmod 400 $PEM_FILE
echo "Created key pair and saved to $PEM_FILE"

# Create a security group
SECURITY_GROUP_ID=$(aws ec2 create-security-group --group-name $SECURITY_GROUP_NAME --description "Security group for $KEY_NAME" --region $REGION --query 'GroupId' --output text)
echo "Created security group $SECURITY_GROUP_NAME with ID $SECURITY_GROUP_ID"

# Allow inbound SSH and TCP 8080
aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 22 --cidr 0.0.0.0/0 --region $REGION
aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 8080 --cidr 0.0.0.0/0 --region $REGION
echo "Configured security group $SECURITY_GROUP_NAME to allow inbound SSH and TCP 8080"

# Launch an EC2 instance
INSTANCE_ID=$(aws ec2 run-instances --image-id $AMI_ID --count 1 --instance-type $INSTANCE_TYPE --key-name $KEY_NAME --security-group-ids $SECURITY_GROUP_ID --region $REGION --block-device-mappings DeviceName=/dev/sda1,Ebs={VolumeSize=$VOLUME_SIZE} --query 'Instances[0].InstanceId' --output text)
if [ -z "$INSTANCE_ID" ]; then
    echo "Failed to launch EC2 instance"
    exit 1
fi
echo "Launched EC2 instance $INSTANCE_ID"

# Tag the instance
aws ec2 create-tags --resources $INSTANCE_ID --tags Key=Name,Value=$KEY_NAME --region $REGION
echo "Tagged instance $INSTANCE_ID with Name=$KEY_NAME"

