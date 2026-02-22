# 12 — Unity Ingestion and Prefabs

## Overview

A Unity Editor script (`MechPartImporter.cs`) receives validated FBX files, imports them, generates prefabs with correct attachment slots, and renders preview thumbnails — all runnable in batchmode from CI.

---

## Importer Script Responsibilities

1. **Import FBX** into `Assets/MechParts/<PartCategory>/`.
2. **Configure import settings**: scale factor 1.0, rig type Generic (no humanoid retarget — rigid binding only), materials extraction set to "Use Embedded Materials" mapped to the project's canonical material assets.
3. **Remap materials**: Map `M_Metal`, `M_Plastic`, `M_Glow`, `M_Detail`, `M_Decal` to existing Unity materials in `Assets/Materials/`.
4. **Create/update prefab**: Instantiate the imported model, attach `AttachmentSlot` components to socket transforms, save as prefab.
5. **Render thumbnail**: Position a camera, render a 512×512 PNG.
6. **Log results**: Write successes and errors to `unity_import_log.txt`.

---

## `MechPartImporter.cs`

```csharp
using UnityEditor;
using UnityEngine;
using System.IO;

public static class MechPartImporter
{
    // Entry point for batchmode: -executeMethod MechPartImporter.ImportAndBuild
    public static void ImportAndBuild()
    {
        string part = GetArg("-part");      // e.g. "LeftArm"
        string version = GetArg("-version"); // e.g. "v001"

        string fbxPath = $"Assets/MechParts/{part}/{part}_{version}.fbx";
        string prefabPath = $"Assets/Prefabs/{part}_{version}.prefab";
        string thumbPath = $"Assets/Thumbnails/{part}_{version}.png";

        // 1. Force reimport
        AssetDatabase.ImportAsset(fbxPath, ImportAssetOptions.ForceUpdate);

        // 2. Configure importer
        var importer = AssetImporter.GetAtPath(fbxPath) as ModelImporter;
        if (importer != null)
        {
            importer.globalScale = 1f;
            importer.animationType = ModelImporterAnimationType.Generic;
            importer.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;
            importer.SaveAndReimport();
        }

        // 3. Instantiate and build prefab
        var modelAsset = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        var instance = Object.Instantiate(modelAsset);
        instance.name = $"{part}_{version}";

        // Remap materials
        RemapMaterials(instance);

        // Setup attachment slots
        SetupSlots(instance);

        // Save prefab
        PrefabUtility.SaveAsPrefabAsset(instance, prefabPath);
        Object.DestroyImmediate(instance);

        // 4. Render thumbnail
        RenderThumbnail(prefabPath, thumbPath);

        Debug.Log($"[MechPartImporter] Completed: {part} {version}");
    }

    static void RemapMaterials(GameObject root)
    {
        string[] approved = { "M_Metal", "M_Plastic", "M_Glow", "M_Detail", "M_Decal" };
        foreach (var renderer in root.GetComponentsInChildren<Renderer>())
        {
            var mats = renderer.sharedMaterials;
            for (int i = 0; i < mats.Length; i++)
            {
                string matName = mats[i]?.name?.Replace(" (Instance)", "");
                string matPath = $"Assets/Materials/{matName}.mat";
                var projectMat = AssetDatabase.LoadAssetAtPath<Material>(matPath);
                if (projectMat != null)
                    mats[i] = projectMat;
                else
                    Debug.LogWarning($"Material not found: {matPath}");
            }
            renderer.sharedMaterials = mats;
        }
    }

    static void SetupSlots(GameObject root)
    {
        foreach (var t in root.GetComponentsInChildren<Transform>())
        {
            if (t.name.StartsWith("SOCKET_"))
            {
                if (t.GetComponent<AttachmentSlot>() == null)
                    t.gameObject.AddComponent<AttachmentSlot>();
            }
        }
    }

    static void RenderThumbnail(string prefabPath, string outputPath)
    {
        // Load prefab, position camera, render to RenderTexture, save PNG
        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
        // ... (camera setup + ReadPixels + EncodeToPNG)
        // Simplified for documentation
        Debug.Log($"Thumbnail saved: {outputPath}");
    }

    static string GetArg(string name)
    {
        var args = System.Environment.GetCommandLineArgs();
        for (int i = 0; i < args.Length - 1; i++)
            if (args[i] == name) return args[i + 1];
        return "";
    }
}
```

---

## `AttachmentSlot.cs` (Runtime Component)

```csharp
using UnityEngine;

public class AttachmentSlot : MonoBehaviour
{
    public string SlotName => gameObject.name; // e.g. "SOCKET_L_ARM_WEAPON"

    public void Attach(GameObject accessory)
    {
        accessory.transform.SetParent(transform);
        accessory.transform.localPosition = Vector3.zero;
        accessory.transform.localRotation = Quaternion.identity;
    }

    public void Detach()
    {
        foreach (Transform child in transform)
            Destroy(child.gameObject);
    }
}
```

---

## Batchmode Command

```bash
Unity -batchmode -nographics \
  -projectPath /path/to/mech-unity \
  -executeMethod MechPartImporter.ImportAndBuild \
  -part LeftArm \
  -version v001 \
  -logFile /artifacts/unity_import_log.txt \
  -quit
```

---

## Output Locations

| Output | Path | Format |
|---|---|---|
| Imported FBX | `Assets/MechParts/<Part>/<Part>_<ver>.fbx` | FBX (binary) |
| Prefab | `Assets/Prefabs/<Part>_<ver>.prefab` | Unity prefab |
| Thumbnail | `Assets/Thumbnails/<Part>_<ver>.png` | PNG 512×512 |
| Import log | `unity_import_log.txt` (CI artifact) | Plain text |

---

## CI Commit-Back vs Artifacts

| Approach | Pros | Cons | MVP Choice |
|---|---|---|---|
| **CI commits prefabs back to `mech-unity` repo** | Repo always has latest prefabs | Requires bot push access, merge conflicts | ❌ |
| **CI stores prefabs as pipeline artifacts** | Simple, no repo mutation | Must download manually or via API | ✅ |

**MVP**: Prefabs and thumbnails are stored as **CI pipeline artifacts**, downloadable via GitLab API. Post-MVP, CI can commit them to `mech-unity`.
