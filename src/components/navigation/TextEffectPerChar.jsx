import React from 'react';
import { TextEffect } from '../core/text-effect';

export function TextEffectPerChar({
  children = "Turn Customer Friction Into High-Impact Engineering Actions",
  className = "text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-slate-900 font-sans leading-tight",
  as = "h1",
}) {
  return (
    <TextEffect per="char" preset="fade" as={as} className={className}>
      {children}
    </TextEffect>
  );
}

export default TextEffectPerChar;
