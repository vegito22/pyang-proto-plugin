# pyang-proto-plugin
Usage is simple add the proto.py in the pyang/plugins directory.
Invoke the proto plugin like other pyang plugin (e.g tree)
Usage example
pyang -p ../public/release/models/ --plugindir=./pyang/plugins/ -f proto ../public/release/models/rpc/openconfig-rpc-api.yang 

/*
 * This module documents a set of RPCs recommended for network
 * management systems (NMS) based on OpenConfig models and
 * conventions. The RPCs are intended to offer guidance for server
 * implementors as a reference for service endpoints which can meet
 * requirements for configuration and telemetry.
 * 
 * Actual implementations may provide slightly different variations
 * on parameters, naming, etc., or extensions which add additional
 * service endpoints.
 */
service openconfig-rpc-api{
	/*
	 * Returns a repeated structure of supported data models
	 */
	rpc getModels(getModelsRequest) (getModelsResponse) {}

}

/*
 * Base identity for supported schema formats
 */
enum openconfig-schema-format-types {
	/*
	 * JSON-Schema
	 */
	json-schema = 0
	/*
	 * YANG model
	 */
	yang-schema = 1
	/*
	 * XML Schema Definition
	 */
	xsd-schema = 2
}

/*
 * Base identity for supported encoding for configuration and
 * operational state data
 */
enum openconfig-data-encoding-types {
	/*
	 * XML encoding
	 */
	encoding-xml = 0
	/*
	 * JSON encoded based on IETF draft standard
	 */
	encoding-json-ietf = 1
	/*
	 * Protocol buffers v3
	 */
	encoding-proto3 = 2
}

/*
 * Base identity for schema retrieval modes
 */
enum openconfig-schema-mode-types {
	/*
	 * Retrieve schema using a supplied URI
	 */
	uri-mode = 0
	/*
	 * Schema delivered in a file
	 */
	file-mode = 1
}

/*
 * Returns a repeated structure of supported data models
 */
message getModelsRequest {
		/*
		 * Schema format requested, e.g., JSON-Schema, XSD, Proto,
		 * YANG
		 */
		openconfig-schema-format-types schema-format = 1;
		/*
		 * Mode for delivering the schema data
		 */
		openconfig-schema-mode-types request-mode = 2;
}

/*
 * Returns a repeated structure of supported data models
 */
message getModelsResponse {
		message schema {
			/*
			 * Name of the corresponding YANG module
			 */
			string model-name = 1;
			/*
			 * Namespace the model belongs to, whether standard or ad-hoc
			 */
			string model-namespace = 2;
			/*
			 * Model version -- for YANG models this should be at least the
			 * 'revision' but could also include a more conventional
			 * version number
			 */
			string model-version = 3;
			/*
			 * Model data, formatted according to the requested format
			 * (e.g., JSON-Schema, YANG, etc.) and using the requested
			 * mode (URI, file, etc.)
			 */
			string model-data = 4;
		}
		/*
		 * list of supported schemas
		 */
		repeated schema schema-list = 1;
}

