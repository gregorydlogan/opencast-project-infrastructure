#!/bin/sh
# Opencast major version
opencast_version=6

# Number of the most recent AMIs to keep
keep=2

get_old_amis ()
{
  ami_name=$1
  aws ec2 describe-images --owner "self" --filters "Name=name,Values=${ami_name}*" --output json |
   jq -r ".Images | sort_by(.CreationDate) | .[0:-${keep}] | .[] | .ImageId + \" \" + .BlockDeviceMappings[].Ebs.SnapshotId"
}

remove_amis_and_snapshots ()
{
  image_type=$1
  ami_name=opencast${opencast_version}-$image_type
  echo "INFO: remove AMIs and Snaphots for $ami_name"

  get_old_amis $ami_name | while read ami_id snap_id
  do
    echo "INFO: remove AMI $ami_id"
    aws ec2 deregister-image --image-id $ami_id $DRYRUN
    echo "INFO: remove snapshot $snap_id"
    aws ec2 delete-snapshot --snapshot-id $snap_id $DRYRUN
  done
}
remove_amis_and_snapshots "allinone"
