import boto3

awsRegion = 'us-east-1'

client = boto3.client('lambda', region_name=awsRegion)

def get_versions(func_name):
    version_list = []
    version_paginator = client.get_paginator('list_versions_by_function')

    try: 
        versions = version_paginator.paginate(FunctionName=func_name)
        for version in versions:
            for v in version['Versions']:
                if v['Version'] != '$LATEST':
                    version_list.append(int(v['Version']))
    
    except Exception as error:
        print('An error occurred getting the function versions:')
        print(str(error))
        raise


    return version_list


def get_lambda_funcs():
    lambda_list = []
    paginator = client.get_paginator('list_functions')
    lambda_funcs = paginator.paginate()


    for func in lambda_funcs:
        for function in func['Functions']:
            lambda_item = {
                'FuncName': function['FunctionName'],
                'Versions' : get_versions(function['FunctionName'])
            }
            lambda_list.append(lambda_item)
    return lambda_list


def delete_old_versions():
    for function in get_lambda_funcs():
        if len(function['Versions']) > 2:
            versions_to_delete = sorted(function['Versions'])[:-2]
            print(function['FuncName'],len(function['Versions']), versions_to_delete)

            # Deletion Part
            for version in versions_to_delete:
                if version != '$LATEST':
                    client.delete_function(
                        FunctionName=function['FuncName'],
                        Qualifier=str(version)
                    )
                else:
                    print("Not deleting default version")

delete_old_versions()


def lambda_handler(event, context):
    delete_old_versions()