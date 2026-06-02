float hash12(vec2 p) {
  vec3 p3 = fract(vec3(p.xyx) * 0.1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.x + p3.y) * p3.z);
}

vec2 normalizeCoord(vec2 value, float isPosition) {
  return (value * 2.0 - (iResolution.xy * isPosition)) / iResolution.y;
}

float boxMask(vec2 p, vec2 center, vec2 halfSize, float feather) {
  vec2 d = abs(p - center) - halfSize;
  float outside = length(max(d, 0.0));
  float inside = min(max(d.x, d.y), 0.0);
  return 1.0 - smoothstep(0.0, feather, outside + inside);
}

float luminance(vec3 color) {
  return dot(color, vec3(0.299, 0.587, 0.114));
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
  vec2 uv = fragCoord.xy / iResolution.xy;
  vec4 source = texture(iChannel0, uv);

  float age = iTime - iTimeCursorChange;
  const float DURATION = 0.18;
  float life = 1.0 - smoothstep(0.0, DURATION, age);

  if (life <= 0.001) {
    fragColor = source;
    return;
  }

  vec2 p = normalizeCoord(fragCoord, 1.0);
  vec2 offsetFactor = vec2(-0.5, 0.5);

  vec4 currentCursor = vec4(
    normalizeCoord(iCurrentCursor.xy, 1.0),
    normalizeCoord(iCurrentCursor.zw, 0.0)
  );
  vec4 previousCursor = vec4(
    normalizeCoord(iPreviousCursor.xy, 1.0),
    normalizeCoord(iPreviousCursor.zw, 0.0)
  );

  vec2 currentCenter = currentCursor.xy - (currentCursor.zw * offsetFactor);
  vec2 previousCenter = previousCursor.xy - (previousCursor.zw * offsetFactor);
  vec2 midPoint = mix(previousCenter, currentCenter, 0.5);
  float travel = distance(previousCenter, currentCenter);

  vec2 cursorSize = max(abs(currentCursor.zw), vec2(0.001));
  vec2 halfSize = vec2((travel * 0.5) + cursorSize.x * 2.0, cursorSize.y * 0.95);
  float region = boxMask(p, midPoint, halfSize, 0.006);

  vec3 bg = iBackgroundColor;
  float ink = smoothstep(0.055, 0.18, distance(source.rgb, bg));
  float amount = region * ink * life;

  if (amount <= 0.001) {
    fragColor = source;
    return;
  }

  vec2 cellSize = max(abs(iCurrentCursor.zw), vec2(8.0, 14.0));
  vec2 cell = floor(fragCoord.xy / cellSize);
  float seed = floor(iTime * 42.0);
  float rnd = hash12(cell + seed);
  float rowRnd = hash12(vec2(cell.y, seed));

  vec2 jitter = vec2(
    (rnd - 0.5) * cellSize.x * 0.86,
    (rowRnd - 0.5) * cellSize.y * 0.22
  ) / iResolution.xy;

  vec2 scrambledUv = clamp(uv + jitter * amount, vec2(0.0), vec2(1.0));
  vec4 scrambled = texture(iChannel0, scrambledUv);

  float split = (hash12(cell.yx + seed) - 0.5) * 0.7 * amount / iResolution.x;
  vec3 chroma = vec3(
    texture(iChannel0, clamp(scrambledUv + vec2(split, 0.0), vec2(0.0), vec2(1.0))).r,
    scrambled.g,
    texture(iChannel0, clamp(scrambledUv - vec2(split, 0.0), vec2(0.0), vec2(1.0))).b
  );

  vec3 accent = mix(iForegroundColor, iCurrentCursorColor.rgb, 0.45);
  vec3 color = mix(source.rgb, chroma, amount * 0.58);
  color = mix(color, accent, amount * 0.08 * step(0.78, rnd));

  fragColor = vec4(color, source.a);
}
