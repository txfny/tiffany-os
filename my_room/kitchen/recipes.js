// the kitchen — Tiffany's recipes. greek-yogurt-forward, protein-powder-free.
// hand-kept (not auto-generated). add a recipe: just tell Claude "add this to the kitchen."
//
// macros are honest estimates, not lab numbers — they move with brands and how
// heavy your scoops are. the point is the shape of the meal, not a to-the-gram audit.
//
// the rule of this kitchen: NO protein powder. where a recipe called for a scoop,
// it's rebuilt around greek yogurt (+ egg whites for structure) so it's real food
// and still lands high-protein. each swap is noted so you know the tradeoff.

window.RECIPES = {
  generated_at: "2026-06-25",
  note: "no protein powder in here — greek yogurt does the heavy lifting.",
  recipes: [

    {
      id: "oreo-baked-oats",
      name: "oreo baked oats",
      emoji: "🍪",
      category: "baked oats",
      blurb: "the one you saved — split chocolate + cookies-and-cream baked oats, rebuilt without the scoop.",
      time: "25 min",
      yields: "1 ramekin",
      no_powder: true,
      macros: { cal: 370, protein: 26, fiber: 6, per: "the whole ramekin (est.)" },
      ingredients: [
        "50g oat flour (or ½ cup oats blended fine)",
        "150g (about ⅔ cup) nonfat greek yogurt — replaces the protein powder",
        "1 egg white (keeps it from going dense without the scoop)",
        "~60ml milk of choice (less than the original — the yogurt brings the moisture)",
        "½ tsp baking powder",
        "5g (1 tsp) cocoa powder — kept separate",
        "1 Oreo (sugar-free if you like)",
        "1 small square dark chocolate",
        "splash vanilla, sweetener to taste (optional)"
      ],
      steps: [
        "Heat oven to 180°C / 350°F.",
        "Mix everything except the cocoa into a batter — oat flour, greek yogurt, egg white, milk, baking powder, vanilla. Crush half the Oreo and stir it in.",
        "Scoop half the batter into a second bowl and mix the cocoa into that half, so you've got a plain side and a chocolate side.",
        "In an oven-safe ramekin, pour the two batters into opposite halves for the half-and-half look.",
        "Press the dark chocolate square into the middle; crumble the other half of the Oreo on top.",
        "Bake 20–25 min, until set and a toothpick comes out with moist crumbs."
      ],
      swap: "Original called for 30g protein powder (vegan, for moisture). Swapped for greek yogurt + an egg white — moist, real food, still high protein. Protein lands a touch lower than the powder version (~26g vs ~30g); add a second egg white to bring it back.",
      source: { label: "adapted from a reel", url: "" }
    },

    {
      id: "everyday-baked-oats",
      name: "everyday baked oats",
      emoji: "🍰",
      category: "baked oats",
      blurb: "your go-to protein cake, scoop swapped for more greek yogurt. mug it or bake it.",
      time: "20 min (or 90s in the microwave)",
      yields: "1 serving",
      no_powder: true,
      macros: { cal: 210, protein: 26, fiber: 4, per: "without blueberries (est.)" },
      ingredients: [
        "⅓ cup egg whites",
        "½ cup nonfat greek yogurt (up from ¼ — this is what replaces the scoop)",
        "½ cup oats (blend to flour if you want it more cake-y)",
        "½ tsp baking powder",
        "cinnamon, to taste",
        "splash vanilla + sweetener to taste",
        "optional: 1 whole egg for extra lift",
        "optional: ¾ cup blueberries (+~40 cal, +15g fiber? no — +~4g fiber)"
      ],
      steps: [
        "Heat oven to 180°C / 350°F (or skip the oven and microwave a mug for 60–90s).",
        "Blend the oats to flour if you want cake texture; mix everything into a batter.",
        "Pour into a greased ramekin; fold in blueberries if using.",
        "Bake 18–22 min until set, or microwave ~90s for the lazy version."
      ],
      swap: "Original had 1 scoop powder (~+15g protein). Greek yogurt brings most of it back — to fully match the old macros, go ¾ cup yogurt + 1 whole egg.",
      source: { label: "your recipe", url: "" }
    },

    {
      id: "greek-yogurt-pancakes",
      name: "greek yogurt pancakes",
      emoji: "🥞",
      category: "breakfast",
      blurb: "your pancakes, powder swapped for oat flour so they still hold together.",
      time: "10 min",
      yields: "1 short stack",
      no_powder: true,
      macros: { cal: 230, protein: 20, fiber: 3, per: "the stack (est.)" },
      ingredients: [
        "⅓ cup egg whites",
        "¼ cup flavored greek yogurt (a Chobani flavor works great)",
        "¼ cup oat flour — replaces the scoop, gives the batter body",
        "½ tsp baking powder",
        "cinnamon, to taste"
      ],
      steps: [
        "Mix the egg whites and greek yogurt together.",
        "Add the oat flour, baking powder, and cinnamon; mix into a smooth batter.",
        "Cook on a nonstick pan over medium; flip when bubbles open up on top.",
        "Stack 'em. Top with more yogurt or berries."
      ],
      swap: "Original used 1 scoop powder for structure. Oat flour does that job here, and the flavored greek yogurt carries the taste.",
      source: { label: "your recipe", url: "" }
    },

    {
      id: "tiramisu-cups",
      name: "tiramisu cups",
      emoji: "☕",
      category: "treats-ish",
      blurb: "coffee-soaked mug cake crumbled into greek yogurt cream. powder-free rebuild.",
      time: "15 min",
      yields: "1 cup",
      no_powder: true,
      macros: { cal: 240, protein: 22, fiber: 3, per: "the cup (est.)" },
      ingredients: [
        "mug cake: 3 tbsp oat flour",
        "mug cake: 1 egg white",
        "mug cake: 2 tbsp greek yogurt",
        "mug cake: ¼ tsp baking powder + splash vanilla + sweetener",
        "to soak: 2–3 tbsp strong coffee or espresso, cooled",
        "the cream: ½ cup vanilla greek yogurt",
        "to finish: cocoa powder, to dust"
      ],
      steps: [
        "Mix the mug cake ingredients; microwave ~45–60s until set.",
        "Crumble the cake and drizzle the cooled coffee over so it soaks in.",
        "In a glass, layer the coffee-soaked crumble with the vanilla greek yogurt.",
        "Dust the top with cocoa. Chill 10 min if you can wait that long."
      ],
      swap: "Original was a protein-powder mug cake. Rebuilt with oat flour + egg white so it sets into a real spongey base — the greek yogurt is the mascarpone stand-in.",
      source: { label: "your recipe", url: "" }
    },

    {
      id: "blueberry-muffins",
      name: "healthy blueberry muffins",
      emoji: "🫐",
      category: "bakes",
      blurb: "your saved recipe — greek-yogurt based, no powder. add the ingredients in order, it matters.",
      time: "20 min",
      yields: "~12 muffins",
      no_powder: true,
      macros: { cal: 230, protein: 5, fiber: 1, per: "per muffin, makes ~12 (est.)" },
      ingredients: [
        "2 eggs",
        "1 cup greek yogurt",
        "¼ cup milk",
        "2 tsp vanilla extract",
        "½ cup oil",
        "½ cup honey",
        "2 cups flour",
        "1 tsp baking powder",
        "½ tsp baking soda",
        "½ tsp salt",
        "1½ cups frozen blueberries"
      ],
      steps: [
        "Heat oven to 425°F (220°C); line a muffin tin.",
        "Add everything in the order listed — eggs, greek yogurt, milk, vanilla, oil, honey, then the flour, baking powder, baking soda, salt. Mix until just combined.",
        "Fold in the frozen blueberries last.",
        "Divide into the cups. Bake at 425°F for 10 min, then drop to 350°F (175°C) for the last 10 min — 20 min total.",
        "Cool before you pull them out so they hold together."
      ],
      swap: "Already powder-free — greek yogurt is built in. Heads up: the ½ cup oil + ½ cup honey make these a wholesome treat more than a protein hit (~5g protein each). Want a higher-protein version? Swap half the oil for extra greek yogurt and cut the honey to ⅓ cup.",
      source: { label: "@brooke.saf", url: "" }
    },

    {
      id: "greek-yogurt-bagels",
      name: "greek yogurt bagels",
      emoji: "🥯",
      category: "bakes",
      blurb: "the My Protein Pantry bagels — already powder-free, greek yogurt is the whole trick.",
      time: "40 min",
      yields: "4 bagels",
      no_powder: true,
      macros: { cal: 149, protein: 11, fiber: 1, per: "per bagel (from the recipe)" },
      ingredients: [
        "1 cup bread flour (or self-rising flour), plus more to dust",
        "1 cup (~245g) Fage nonfat plain greek yogurt — thick is key, less sticky dough",
        "2 tsp baking powder (skip if using self-rising flour)",
        "½ tsp salt",
        "1 egg, beaten, for the egg wash",
        "everything bagel seasoning (optional)"
      ],
      steps: [
        "Heat oven to 190°C / 375°F; line a tray.",
        "Whisk flour, baking powder, and salt. Stir in the greek yogurt until a shaggy dough forms.",
        "Knead on a floured counter 1–2 min until smooth.",
        "Divide into 4; roll each into a rope and pinch the ends into a ring.",
        "Brush with egg wash; sprinkle seasoning.",
        "Bake 27–30 min until risen and golden."
      ],
      swap: "Nothing to swap — these are greek-yogurt-based by design. Exactly your no-powder vibe.",
      source: { label: "My Protein Pantry", url: "https://myproteinpantry.com/high-protein-bagles/" }
    },

    {
      id: "protein-cookies",
      name: "greek yogurt protein cookies",
      emoji: "🍪",
      category: "treats-ish",
      blurb: "chewy oat + nut-butter cookies, protein from greek yogurt and the egg — no scoop.",
      time: "20 min",
      yields: "8 cookies",
      no_powder: true,
      macros: { cal: 110, protein: 5, fiber: 2, per: "per cookie (est.)" },
      ingredients: [
        "1 cup oats (blend half to flour)",
        "¼ cup greek yogurt",
        "¼ cup nut butter (peanut or almond)",
        "1 egg",
        "sweetener to taste + splash vanilla",
        "½ tsp baking powder + pinch salt",
        "2–3 tbsp dark chocolate chips"
      ],
      steps: [
        "Heat oven to 180°C / 350°F; line a tray.",
        "Mix everything into a thick dough; fold in the chocolate chips.",
        "Scoop into 8 mounds, flatten slightly (they don't spread much).",
        "Bake 10–12 min until the edges set. Let them firm up before moving."
      ],
      swap: "Protein comes from greek yogurt + egg + nut butter instead of powder. Lower protein-per-cookie than a powder bar, but real-food chewy.",
      source: { label: "kitchen original", url: "" }
    },

    {
      id: "protein-bar-bowl",
      name: "protein bar breakfast bowl",
      emoji: "🍫",
      category: "breakfast",
      blurb: "your quick assembly, scoop swapped for a greek yogurt base. zero cooking.",
      time: "3 min",
      yields: "1 bowl",
      no_powder: true,
      macros: { cal: 330, protein: 33, fiber: 15, per: "the bowl (est.)" },
      ingredients: [
        "1 protein bar, chopped",
        "¾ cup nonfat greek yogurt — replaces the scoop of powder",
        "splash of Fairlife milk",
        "½ cup blueberries"
      ],
      steps: [
        "Spoon the greek yogurt into a bowl; loosen with a splash of Fairlife.",
        "Top with the chopped protein bar and the blueberries.",
        "That's it. Stir or layer, your call."
      ],
      swap: "Dropped the scoop of powder; greek yogurt carries the protein and the creaminess. Lands around the same ~33g — basically a loaded yogurt bowl now.",
      source: { label: "your recipe", url: "" }
    },

    {
      id: "chocolate-date-cake",
      name: "chocolate date cake",
      emoji: "🍫",
      category: "treats-ish",
      blurb: "not a macro recipe — a real treat you loved. dates + cocoa, naturally powder-free.",
      time: "40 min",
      yields: "1 small pan",
      no_powder: true,
      macros: { cal: 0, protein: 0, fiber: 0, per: "a treat — eat it because it's good 🤍" },
      ingredients: [
        "brownies: 10 medjool dates",
        "brownies: ¾ cup water + ½ tsp baking soda (to soften the dates)",
        "brownies: 2 eggs",
        "brownies: ⅓ cup yogurt",
        "brownies: 2 tbsp maple syrup + 1 tsp vanilla + ½ tsp cinnamon",
        "brownies: ½ cup milk",
        "brownies: ½ cup almond flour + ½ cup spelt flour",
        "brownies: ¾ cup cocoa powder",
        "brownies: 1½ tsp baking powder + ½ tsp baking soda + ½ tsp salt",
        "glaze: 2 tbsp cocoa powder + 1 tbsp tahini + 1 tbsp coconut oil + 1 tbsp maple syrup"
      ],
      steps: [
        "Blend or mash the dates with the water + ½ tsp baking soda into a smooth paste.",
        "Mix in the eggs, yogurt, maple, vanilla, cinnamon, and milk.",
        "Fold in the almond flour, spelt flour, cocoa, baking powder, baking soda, and salt.",
        "Pour into a lined pan; bake at 190°C / 375°F for 24–27 min, until a toothpick shows wet crumbs.",
        "Whisk the glaze and spread it over once cooled."
      ],
      swap: "Already powder-free. This one's filed as a treat, not a protein hit — it's here because you said it's one of the best things you've made.",
      source: { label: "saved from a reel", url: "" }
    }

  ]
};
