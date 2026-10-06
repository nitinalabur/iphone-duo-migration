import CoreGraphics

let cases: [(String, CGSize, [CGRect], Bool)] = [
    ("narrow flat window", CGSize(width: 400, height: 800), [], false),
    ("wide flat window", CGSize(width: 900, height: 700), [], true),
    ("short flat window", CGSize(width: 900, height: 350), [], false),
    ("expanded boundary", CGSize(width: 700, height: 500), [], true),
    ("fold through window", CGSize(width: 600, height: 800), [CGRect(x: 290, y: 0, width: 20, height: 800)], true),
    ("horizontal fold through window", CGSize(width: 500, height: 700), [CGRect(x: 0, y: 340, width: 500, height: 20)], true),
    ("fold at left edge", CGSize(width: 400, height: 800), [CGRect(x: 0, y: 0, width: 20, height: 800)], false),
    ("fold at right edge", CGSize(width: 400, height: 800), [CGRect(x: 380, y: 0, width: 20, height: 800)], false),
    ("fold outside window", CGSize(width: 400, height: 800), [CGRect(x: 420, y: 0, width: 20, height: 800)], false),
    ("fold outside visible height", CGSize(width: 400, height: 800), [CGRect(x: 190, y: 900, width: 20, height: 800)], false),
    ("fold at top edge", CGSize(width: 900, height: 350), [CGRect(x: 0, y: 0, width: 900, height: 20)], false),
    ("fold at bottom edge", CGSize(width: 900, height: 350), [CGRect(x: 0, y: 330, width: 900, height: 20)], false),
    ("too little room before vertical fold", CGSize(width: 600, height: 800), [CGRect(x: 1, y: 0, width: 20, height: 800)], false),
    ("too little room after vertical fold", CGSize(width: 600, height: 800), [CGRect(x: 579, y: 0, width: 20, height: 800)], false),
    ("too little room before horizontal fold", CGSize(width: 500, height: 700), [CGRect(x: 0, y: 1, width: 500, height: 20)], false),
    ("too little room after horizontal fold", CGSize(width: 500, height: 700), [CGRect(x: 0, y: 679, width: 500, height: 20)], false),
    ("narrow horizontal panes", CGSize(width: 200, height: 700), [CGRect(x: 0, y: 340, width: 200, height: 20)], false),
    ("short vertical panes", CGSize(width: 600, height: 100), [CGRect(x: 290, y: 0, width: 20, height: 100)], false),
    ("wide window with cramped fold", CGSize(width: 900, height: 700), [CGRect(x: 1, y: 0, width: 20, height: 700)], false),
    ("tall window with cramped fold", CGSize(width: 900, height: 700), [CGRect(x: 0, y: 1, width: 900, height: 20)], false),
]

for (name, size, divisions, expected) in cases {
    precondition(
        DuoPaneLayout.usesSplitPanes(size: size, activeDivisionFrames: divisions) == expected,
        "Unexpected layout: \(name)"
    )
}
print("\(cases.count) pane-layout cases passed.")
