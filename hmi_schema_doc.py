HMI_SCHEMA_DOC = """
Controller configuration schema (simplified):

- Root object:
  {
    "database": {
      "tags": {
        "<tagName>": {
          "datatype": "number" | "bool" | "string",
          "description": string,
          "unit": string | null,
          "min": number | null,
          "max": number | null
        },
        ...
      },
      "settings": {
        "persistanceUpdateTime": number,
        "maxDaysToLog": number
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
        "viewsTree": array
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
[
  {
    "name": "<tagName>",
    "definition": {
      "datatype": "...",
      "description": "...",
      "unit": null,
      "min": null,
      "max": null
    }
  }
]
"""
