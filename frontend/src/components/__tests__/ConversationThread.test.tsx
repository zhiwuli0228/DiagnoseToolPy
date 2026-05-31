import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ConversationThread from '../ConversationThread';
import type { ConversationTurn } from '../../types/api';

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

const mockTurn: ConversationTurn = {
  turn_id: '001',
  user_context: {
    phenomenon: 'Service is slow',
    stack: 'java.lang.ThreadPool...',
    params: 'timeout=30',
  },
  evidence_refs: ['log-1'],
  mode: 'user-priority',
  timestamp: new Date().toISOString(),
};

describe('ConversationThread', () => {
  it('shows empty state message when no turns and no question', () => {
    renderWithRouter(
      <ConversationThread turns={[]} currentQuestion={null} />
    );
    expect(screen.getByText('输入问题描述和选择日志证据后，点击"开始诊断"发起对话')).toBeInTheDocument();
  });

  it('renders user context with all fields', () => {
    const turn: ConversationTurn = {
      ...mockTurn,
      ai_diagnosis: undefined,
      ai_question: undefined,
    };

    renderWithRouter(
      <ConversationThread turns={[turn]} />
    );

    expect(screen.getByText('## 现象')).toBeInTheDocument();
    expect(screen.getByText('Service is slow')).toBeInTheDocument();
    expect(screen.getByText('## 堆栈')).toBeInTheDocument();
    expect(screen.getByText('## 入参')).toBeInTheDocument();
    expect(screen.getByText('timeout=30')).toBeInTheDocument();
  });

  it('renders AI diagnosis when present', () => {
    const turn: ConversationTurn = {
      ...mockTurn,
      ai_diagnosis: 'Possible memory leak detected',
    };

    renderWithRouter(
      <ConversationThread turns={[turn]} />
    );

    expect(screen.getByText('AI 诊断')).toBeInTheDocument();
    expect(screen.getByText('Possible memory leak detected')).toBeInTheDocument();
  });

  it('renders AI question card when ai_question is present', () => {
    const turn: ConversationTurn = {
      ...mockTurn,
      ai_question: 'What is the error code?',
      ai_diagnosis: undefined,
    };

    renderWithRouter(
      <ConversationThread turns={[turn]} />
    );

    expect(screen.getByText('AI 追问')).toBeInTheDocument();
    expect(screen.getByText('What is the error code?')).toBeInTheDocument();
  });

  it('calls onContinue when reply is submitted', () => {
    const onContinue = vi.fn();
    renderWithRouter(
      <ConversationThread
        turns={[]}
        currentQuestion="What is the stack trace?"
        onContinue={onContinue}
      />
    );

    const textarea = screen.getByPlaceholderText('输入您的回复...');
    fireEvent.change(textarea, { target: { value: 'Here is the stack trace' } });

    const sendButton = screen.getByText('发送回复');
    fireEvent.click(sendButton);

    expect(onContinue).toHaveBeenCalledWith('Here is the stack trace');
  });

  it('calls onSkip when skip button is clicked', () => {
    const onSkip = vi.fn();
    renderWithRouter(
      <ConversationThread
        turns={[]}
        currentQuestion="What is the stack trace?"
        onSkip={onSkip}
        onEnd={vi.fn()}
      />
    );

    const skipButton = screen.getByText('跳过，直接诊断');
    fireEvent.click(skipButton);

    expect(onSkip).toHaveBeenCalled();
  });

  it('renders multiple turns correctly', () => {
    const turns: ConversationTurn[] = [
      {
        turn_id: '001',
        user_context: { phenomenon: 'Error 1', stack: '', params: '' },
        evidence_refs: [],
        ai_question: 'Question 1?',
        mode: 'user-priority',
        timestamp: new Date().toISOString(),
      },
      {
        turn_id: '002',
        user_context: { phenomenon: 'Error 2', stack: '', params: '' },
        evidence_refs: [],
        ai_diagnosis: 'Diagnosis 2',
        mode: 'user-priority',
        timestamp: new Date().toISOString(),
      },
    ];

    renderWithRouter(
      <ConversationThread turns={turns} />
    );

    expect(screen.getByText('Question 1?')).toBeInTheDocument();
    expect(screen.getByText('Diagnosis 2')).toBeInTheDocument();
  });

  it('displays user icon in user message cards', () => {
    const turn: ConversationTurn = {
      ...mockTurn,
      ai_diagnosis: undefined,
      ai_question: undefined,
    };

    renderWithRouter(
      <ConversationThread turns={[turn]} />
    );

    expect(screen.getByText('用户')).toBeInTheDocument();
  });
});
