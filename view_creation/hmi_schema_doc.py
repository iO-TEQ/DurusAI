HMI_SCHEMA_DOC = """
Controller configuration schema (simplified):

- Root object:
  {
    "database": {
      "tags": {
        "<tagName>": {
          "arraydim": number, // default: 1
          "datatype": string, // options: "Text", "Number", default: "Text"
          "value": string | number, // default: "" for "Text", 0 for "Number"
          "config": {
            "persistent": boolean, // default: false
            "historic": boolean, // default: false
            "hidden": boolean, // default: false
            "editable": boolean // default: true
          },
          "comment": string   // default: ""
        },
        ...
      },
      "settings": {
        "persistanceUpdateTime": number, // in seconds, default: 1
        "maxDaysToLog": number // in days, default: 10
      }
    },
    "modules": [
      {
        "id": string,
        "name": string,
        "type": string,
        "config": object
      },
      ...
    ],
    "hmi": {
      "views": [
        {
          "id": string,
          "name": string,
          "type": "view",
          "config": {
            "width": number,
            "height": number,
            "style": object,
            "sizeMode": "normal" | "zoom"
          },
          "components": [
            {
              "id": string,
              "viewId": string,
              "type": string,          // e.g. "label", "button"
              "comptName": string,     // UI name
              "x": number,
              "y": number,
              "w": number,
              "h": number,
              "config": {
                "text"?: string,
                "tagName"?: string,
                "style"?: object
              }
            },
            ...
          ]
        },
        ...
      ],
      "general": {
        "defaultViewId": string | null,
        "mainView": string | null,
        "viewsTree": [
          {
            "name": string,
            "type": "view",
            "id": string
          },
          ...
        ]
      }
    },
    "charts": [
      {
        "id": string,
        "name": string,
        "series": [ { "tag": string, "color": string }, ... ]
      },
      ...
    ]
  }

When you generate proposed_changes.hmi.views, the objects MUST match this schema.
When you generate tags_to_add, use:
{
  "<tagName>": {
    "arraydim": number, // default: 1
    "datatype": string, // options: "Text", "Number", default: "Text"
    "value": string | number, // default: "" for "Text", 0 for "Number"
    "config": {
      "persistent": boolean, // default: false
      "historic": boolean, // default: false
      "hidden": boolean, // default: false
      "editable": boolean // default: true
    },
    "comment": string   // default: ""
  }
}
"""
