import CoreGraphics

// Content breakpoints for this example, not iPhone Duo hardware dimensions.
enum DuoPaneLayout {
    static func usesSplitPanes(size: CGSize, activeDivisionFrames: [CGRect] = []) -> Bool {
        let bounds = CGRect(origin: .zero, size: size)
        let minimumPane = CGSize(width: 240, height: 180)
        let spanningDivisions = activeDivisionFrames.filter { division in
            guard bounds.intersects(division) else { return false }
            // Multitasking can leave an active division at or outside the window edge.
            // Use paired panes only when the window has space on both sides.
            if division.height > division.width {
                return division.minX > bounds.minX && division.maxX < bounds.maxX
            }
            return division.minY > bounds.minY && division.maxY < bounds.maxY
        }
        if !spanningDivisions.isEmpty {
            return spanningDivisions.contains { division in
                if division.height > division.width {
                    return division.minX - bounds.minX >= minimumPane.width
                        && bounds.maxX - division.maxX >= minimumPane.width
                        && size.height >= minimumPane.height
                }
                return division.minY - bounds.minY >= minimumPane.height
                    && bounds.maxY - division.maxY >= minimumPane.height
                    && size.width >= minimumPane.width
            }
        }
        return size.width >= 700 && size.height >= 500
    }
}
