# vopaas_statistics
A service for logging and presenting statistics about the frequency an IDP is used for a
specific SP.

# Run Statistics service

Copy the **settings.cnf.example** and rename the copy to **settings.cnf**. At the moment it's not 
possible to name the configuration anything other then **settings.cfg**.

```shell
    cd vopaas_statistics/server/
    python flask_server.py
```

# Configuration
| Parameter name | Data type | Example value | Description |
| -------------- | --------- | ------------- | ----------- |
| SSL | boolean | True | Should the server use https or not |
| SERVER_CERT | String | "./keys/server.crt" | The path to the certificate file used by SSL comunication |
| SERVER_KEY | String | "./keys/server.key" | The path to the key file used by SSL comunication |
| JWT_PUB_KEY | List of strings | ["./keys/mykey.pub"] | A list of signature verification keys |
| SECRET_SESSION_KEY | String | "t3ijtgglok432jtgerfd" | A random value used by cryptographic components to for example to sign the session cookie |
| PORT | Integer | 8166 | Port on which the CMservice should start |
| HOST | String | "127.0.0.1" | The IP-address on which the CMservice should run |
| DEBUG | boolean | False | Turn on or off the Flask servers internal debuggin, should be turned off to ensure that all log information get stored in the log file |
| DATABASE_CLASS_PATH | String | "cmservice.database.SQLite3ConsentDB" | Specifies which python database class the CMservice should use. Currently there exists two modules DictConsentDB and SQLite3ConsentDB |
| DATABASE_CLASS_PARAMETERS | List of strings | ["test.db"] | Input parameters which should be passed into the database class specified above. SQLite3ConsentDB needs a single parameter, a path where the database should be stored. DictConsentDB does not take any parameters so [] should be specified |
| LOG_FILE | String | "cmservice.log" | A path to the log file, if none exists it will be created |
| LOG_LEVEL | String | "WARNING" | Which logging level the application should use. Possible values: INFO, DEBUG, WARNING, ERROR and CRITICAL |

# Storage

## Stored information 

| Database column | Description |
| --------------- | ----------- |
| sp_name | sp identity (entity id)  |
| idp_name | idp identity (entity id) |
| frequency | The frequency an idp has been used by a specific sp |
| ticket | Approved ticket |
| time_stamp | When a specific ticket was created |

# Presenting the statistic

To look at the statistic go to root of the server (path: /). Here the user can pick a SP of interest
from a list of sp entity ids. 

# Flow

1. Ask the service for a ticket
2. Create a signed JWT containing **{sp, idp, ticket}** and send to the service
3. The service will check the signing and ticket and update the statistics
