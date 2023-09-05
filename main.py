import oci


def get_volumes_sizes(instance_id, availability_domain):
    global storage
    global compute_client
    global blockstorage_client

    # Block Storage
    volume_attachments = compute_client.list_volume_attachments(
        compartment_id, instance_id=instance.id).data

    if len(volume_attachments) == 0:
        storage_size = "N/A"
    else:
        storage_size = 0
        for disk in storage:
            for attachment in volume_attachments:
                if disk.id == attachment.volume_id:
                    storage_size += disk.size_in_gbs

    # Boot Volume
    boot_id = compute_client.list_boot_volume_attachments(
        compartment_id=compartment_id,
        instance_id=instance.id,
        availability_domain=availability_domain).data[0].boot_volume_id
    boot_size = blockstorage_client.get_boot_volume(
        boot_volume_id=boot_id).data.size_in_gbs

    return boot_size, storage_size


config = oci.config.from_file(file_location="./config")

root_compartment_id = config["tenancy"]

identity_client = oci.identity.IdentityClient(config)

list_compartments_response = identity_client.list_compartments(
    compartment_id=root_compartment_id,
    compartment_id_in_subtree=True)

with open(f"Instances-specs.csv", "w+") as file:
    file.write("Compartment, Instance, vCPU, CPU, Memory (GB), Boot Volume Size (GB), Total Block Volume Size (GB), Type, Status \n")
    for compartment in list_compartments_response.data:
        compartment_id = compartment.id
        compartment_name = compartment.name

        compute_client = oci.core.ComputeClient(config)
        blockstorage_client = oci.core.BlockstorageClient(config)

        storage = blockstorage_client.list_volumes(
            compartment_id=compartment_id,
        ).data

        instances = compute_client.list_instances(
            compartment_id=compartment_id).data

        for instance in instances:
            boot, volume_size = get_volumes_sizes(
                instance.id, instance.availability_domain)
            file.write(f'{compartment_name}, {instance.display_name}, {instance.shape_config.vcpus}, "{instance.shape_config.processor_description}", {int(instance.shape_config.memory_in_gbs)}, {boot}, {volume_size}, SSD, {instance.lifecycle_state}\n')
