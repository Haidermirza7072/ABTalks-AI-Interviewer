import type { InterviewMode, Persona } from '../types';

const TECHNICAL_QUESTIONS: Record<number, string> = {
  2: "Nice. Let's go a bit deeper — what is the event loop in JavaScript and how does it handle asynchronous operations?",
  3: 'Good. Next, in React, why are keys important in lists, and what can go wrong if you use array indexes as keys?',
  4: 'Alright, let us think about a scenario: a React component re-renders in an infinite loop. How would you go about debugging that?',
  5: 'Time for a coding question. Write a function that finds the two numbers in an array that sum up to a given target value. You can write code in the editor below.',
  6: 'Great progress! Now talk about performance — how would you optimize a slow React list that renders thousands of rows?',
  7: 'One more technical one: explain the difference between useMemo and useCallback, and when you would reach for each.',
};

const HINTS: Record<number, string> = {
  2: 'Think about the call stack, the task queue, and the microtask queue. Where do Promise callbacks get scheduled?',
  3: 'Imagine reordering a list of rows. What happens to each row local state when the index keys shift?',
  4: 'Check the dependency arrays of your useEffect, and whether state is being updated inside the effect itself.',
  5: 'Use a hash map (Map) to track complements as you iterate. That gives you O(n) time and O(n) space.',
  6: 'Consider React.memo, windowing (react-window / virtualized lists), and moving work out of the render phase.',
  7: 'useMemo caches values, useCallback caches functions. When are fresh references triggering unnecessary child re-renders?',
};

const getFeedbackComment = (score: number): string => {
  if (score >= 8) return 'Strong answer — clear, structured, and on point.';
  if (score >= 6) return 'Solid attempt. Add one concrete example and it is golden.';
  if (score >= 4) return 'Decent coverage, but the structure got loose. Try STAR: Situation, Task, Action, Result.';
  return 'This one was shaky. Pause, take a breath, and structure your answer before diving in.';
};

const pick = <T,>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];

const SKILL_KEYWORDS = [
  'Python', 'FastAPI', 'Django', 'Flask', 'JavaScript', 'TypeScript', 'React', 'Next.js',
  'Node.js', 'Express', 'Java', 'Go', 'C++', 'SQL', 'PostgreSQL', 'MySQL', 'MongoDB',
  'Redis', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'REST', 'GraphQL', 'gRPC',
  'Microservices', 'RabbitMQ', 'Celery', 'LangChain', 'ChromaDB', 'RAG', 'LLM',
  'OpenAI', 'TensorFlow', 'PyTorch', 'Machine Learning', 'Deep Learning', 'Data Science',
  'Pandas', 'NumPy', 'Git', 'CI/CD', 'Pytest', 'Docker Compose',
];

const extractSkills = (resume: string): string[] => {
  const found = SKILL_KEYWORDS.filter((skill) => new RegExp(`\\b${skill.replace(/[.+]/g, '\\$&')}`, 'i').test(resume));
  return Array.from(new Set(found)).slice(0, 3);
};

export const mockApi = {
  startInterview: async (candidateId: string, resumeText: string, mode: InterviewMode) => {
    const resume = resumeText.trim();
    const skills = resume ? extractSkills(resume) : [];
    const firstQuestion = resume
      ? skills.length > 0
        ? `Hello ${candidateId}! I've reviewed your resume and see you've worked with ${skills.join(', ')}. To begin (${mode === 'practice' ? 'practice mode' : 'exam mode'}), tell me about a project where you put those skills to use — what was your specific role and the biggest challenge you solved?`
        : `Hello ${candidateId}! I've reviewed your resume — it mentions "${resume.slice(0, 140)}${resume.length > 140 ? '...' : ''}". To begin (${mode === 'practice' ? 'practice mode' : 'exam mode'}), tell me about the most impactful project you worked on and what your specific role was in it.`
      : `Hello ${candidateId}! Welcome to your ${mode === 'practice' ? 'practice' : 'exam'} interview. To begin, could you explain the concept of Closures in JavaScript?`;

    return new Promise((resolve) => setTimeout(() => resolve({
      session_id: `sess_${Date.now()}`,
      first_question: firstQuestion,
      turn_count: 1,
      can_conclude: false,
      covered_days: ['day_1'],
      current_persona: 'hiring_manager' as Persona,
    }), 1500));
  },

  submitAnswer: async (_sessionId: string, answer: string, currentTurn: number) => {
    const isReadyToConclude = currentTurn >= 7;
    const newPersona: Persona = currentTurn >= 4 ? 'senior_engineer' : 'hiring_manager';

    const score = Math.min(9.5, Math.max(3, 5.5 + (answer?.length ?? 0) / 150));
    const roundedScore = Math.round(score * 10) / 10;

    const next_question =
      TECHNICAL_QUESTIONS[currentTurn + 1] ??
      pick([
        'Great. Final scenario: describe a time you had to refactor a large, messy codebase. What was your approach?',
        'Nice work today. One last question: how do you stay up to date with new technologies and decide what to learn next?',
      ]);

    return new Promise((resolve) => setTimeout(() => resolve({
      next_question,
      turn_count: currentTurn + 1,
      can_conclude: isReadyToConclude,
      covered_days: ['day_1', 'day_3'],
      current_persona: newPersona,
      is_coding: /write a function|code in the editor/i.test(next_question),
      answer_feedback: {
        score: roundedScore,
        comment: getFeedbackComment(roundedScore),
      },
    }), 2500));
  },

  getHint: async (_sessionId: string, question: string) => {
    const hints: Array<[RegExp, string]> = [
      [/sum|target/i, HINTS[5]],
      [/useMemo|useCallback|memo/i, HINTS[7]],
      [/optimize|slow/i, HINTS[6]],
      [/infinite loop|re-render/i, HINTS[4]],
      [/keys/i, HINTS[3]],
      [/event loop/i, HINTS[2]],
    ];
    const hint =
      hints.find(([re]) => re.test(question))?.[1] ??
      'Break the problem into smaller pieces, speak your reasoning out loud, and aim for a clean, structured answer.';

    return new Promise((resolve) => setTimeout(() => resolve({ hint }), 900));
  },

  getFeedback: async (_sessionId: string) => {
    return new Promise((resolve) => setTimeout(() => resolve({
      readiness_score: 8.5,
      strengths: [
        { title: 'Strong Core Knowledge', evidence: '"A closure is the combination of a function bundled together with references to its surrounding state."' },
        { title: 'React Hooks Mastery', evidence: '"Using useEffect cleanup functions is critical to prevent memory leaks."' }
      ],
      growth_areas: [
        { title: 'System Design Patterns', resource: 'Review Curriculum Day 12: Scalable Architecture' }
      ],
      communication_tips: [
        'Try to structure your answers using the STAR method for behavioral questions.',
        'Be more concise when explaining basic definitions.'
      ],
      evidence_citations: [
        'Transcript Turn 1: Defined closures accurately.',
        'Transcript Turn 3: Addressed memory leaks with solid React fundamentals.'
      ],
      is_partial: false
    }), 3000));
  },

  abortInterview: async (_sessionId: string) => {
    return new Promise((resolve) => setTimeout(() => resolve({
      readiness_score: null,
      strengths: [
        { title: 'Initiative', evidence: 'Started the interview proactively.' }
      ],
      growth_areas: [
        { title: 'Completion', resource: 'Try to complete the full 8-turn interview next time.' }
      ],
      communication_tips: [],
      evidence_citations: [],
      is_partial: true,
      disclaimer: 'This feedback is based on an incomplete interview session.'
    }), 1500));
  }
};
