// Illustrative layout; include DuoPaneLayout.swift and connect your model and persistence.
import SwiftUI

@available(iOS 15.0, *)
struct DuoReviewExample: View {
    @State private var draft = ""
    @State private var selectedReference = 0

    var body: some View {
        if #available(iOS 27.1, *) {
            GeometryReader { geometry in
                let divisions = geometry
                    .reservedRegions(kind: .division)
                    .filter(\.isActive).map(\.frame)

                if DuoPaneLayout.usesSplitPanes(size: geometry.size, activeDivisionFrames: divisions) {
                    ArrangementView {
                        Form { editorFields }
                    } secondary: {
                        ScrollView { referenceContent.padding() }
                    }
                    .arrangementViewStyle(.split)
                } else {
                    compactContent
                }
            }
        } else {
            compactContent
        }
    }

    private var compactContent: some View {
        Form {
            Section("Edit") { editorFields }
            Section("Reference") { referenceContent }
        }
    }

    private var editorFields: some View {
        TextEditor(text: $draft)
            .frame(minHeight: 96)
            .accessibilityLabel("Notes")
    }

    private var referenceContent: some View {
        VStack(alignment: .leading, spacing: 16) {
            Picker("Reference", selection: $selectedReference) {
                Text("Photo").tag(0)
                Text("Document").tag(1)
            }
            Image(systemName: selectedReference == 0 ? "photo" : "doc.text")
                .resizable()
                .scaledToFit()
                .frame(maxWidth: 240, maxHeight: 240)
                .accessibilityLabel("Selected reference preview")
        }
    }
}
